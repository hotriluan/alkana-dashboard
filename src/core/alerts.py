"""
Alert System - Detect stuck inventory and low yield

Alerts:
1. Stuck in Transit: Goods received but not issued within 48 hours
2. Low Yield: Production yield below 85%
"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.config import STUCK_IN_TRANSIT_HOURS, LOW_YIELD_THRESHOLD
from src.core.netting import StackNettingEngine


@dataclass
class Alert:
    """Alert data structure"""
    alert_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM
    entity_type: str  # BATCH, ORDER
    entity_id: str
    batch: Optional[str]
    material: Optional[str]
    plant: Optional[int]
    metric_value: float
    threshold: float
    message: str
    detected_at: datetime


class AlertDetector:
    """
    Alert Detection System
    
    Detects:
    1. Stuck in Transit: MVT 101 without corresponding MVT 601 within threshold
    2. Low Yield: Production yield below threshold
    """
    
    def __init__(
        self,
        mb51_df: pd.DataFrame,
        production_chain_df: Optional[pd.DataFrame] = None,
        stuck_threshold_hours: int = STUCK_IN_TRANSIT_HOURS,
        yield_threshold_pct: float = LOW_YIELD_THRESHOLD,
        uom_converter = None
    ):
        self.netting_engine = StackNettingEngine(mb51_df)
        self.mb51_df = mb51_df
        self.production_chain_df = production_chain_df
        self.stuck_threshold = stuck_threshold_hours
        self.yield_threshold = yield_threshold_pct
        self.uom_converter = uom_converter
    
    def detect_stuck_in_transit(self, plant: int = 1401) -> List[Alert]:
        """
        Detect delayed transit from Factory to DC
        
        Transit Time = Time from production finish to DC receipt
        
        Logic:
        1. Get P01 batches from FactProduction with actual_finish_date
        2. Find MVT 101 (Goods Receipt) at Plant 1401 for each batch
        3. Calculate transit_hours = MVT 101 posting_date - actual_finish_date
        4. If transit_hours > threshold → DELAYED_TRANSIT alert
        
        Note: Transit time is from production completion to DC receipt,
        NOT from DC receipt to DC issue (that would be storage time).
        
        IMPORTANT: Only applies to P01 (Finished Goods)
        - P02/P03 (Semi-finished) don't go to finished goods warehouse
        """
        alerts = []
        current_time = datetime.now()
        
        # Get P01 batches with production finish dates from database
        from src.db.models import FactProduction
        from src.db.connection import SessionLocal
        
        db = SessionLocal()
        try:
            # Get P01 batches with actual finish dates
            p01_batches = db.query(
                FactProduction.batch,
                FactProduction.actual_finish_date,
                FactProduction.material_code
            ).filter(
                FactProduction.mrp_controller == 'P01',
                FactProduction.batch.isnot(None),
                FactProduction.actual_finish_date.isnot(None)
            ).all()
            
            for batch_row in p01_batches:
                batch = batch_row.batch
                actual_finish_date = batch_row.actual_finish_date
                material = batch_row.material_code
                
                # Convert to datetime if it's a date
                if isinstance(actual_finish_date, datetime):
                    finish_dt = actual_finish_date
                else:
                    finish_dt = datetime.combine(actual_finish_date, datetime.min.time())
                
                # Get MVT 101 receipt date at Plant 1401 (after netting 101/102)
                result_101 = self.netting_engine.apply_stack_netting(batch, plant, 101, 102)
                
                if result_101.is_fully_reversed:
                    continue  # No valid receipt
                
                receipt_date = result_101.last_valid_date
                if receipt_date is None:
                    continue
                
                # Calculate transit time from production finish to DC receipt
                transit_hours = (receipt_date - finish_dt).total_seconds() / 3600
                
                # Only alert if transit time exceeded threshold
                if transit_hours > self.stuck_threshold:
                    severity = self._get_stuck_severity(transit_hours)
                    alerts.append(Alert(
                        alert_type='DELAYED_TRANSIT',
                        severity=severity,
                        entity_type='BATCH',
                        entity_id=batch,
                        batch=batch,
                        material=material,
                        plant=plant,
                        metric_value=round(transit_hours, 1),
                        threshold=self.stuck_threshold,
                        message=f"Batch {batch} transit delayed {round(transit_hours, 1)} hours (Factory → DC)",
                        detected_at=current_time
                    ))
        finally:
            db.close()
        
        
        return alerts
    
    def _get_stuck_severity(self, hours: float) -> str:
        """Determine alert severity based on hours stuck"""
        if hours > 72:
            return 'CRITICAL'
        elif hours > 48:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def detect_low_yield(self) -> List[Alert]:
        """
        Detect low P02→P01 yield using dual validation
        
        Logic:
        1. Sequential batch pattern: P01 = P02 - 1
        2. Material name validation: P01 starts with P02 + suffix
        3. Yield calculation: (P01 KG / P02 KG) × 100
        
        Coverage: ~31% of P02 batches (406 valid pairs)
        """
        alerts = []
        
        # Import P02→P01 yield calculator
        from src.core.p02_p01_yield import calculate_p02_p01_yield
        
        # Get all P02 batches (MVT 261 @ Plant 1201)
        p02_batches = self.mb51_df[
            (self.mb51_df['col_1_mvt_type'] == 261) &
            (self.mb51_df['col_2_plant'] == 1201)
        ]['col_6_batch'].unique()
        
        current_time = datetime.now()
        
        for p02_batch in p02_batches:
            if not p02_batch:
                continue
            
            # Calculate yield using dual validation
            yield_data = calculate_p02_p01_yield(
                p02_batch,
                self.mb51_df,
                self.uom_converter
            )
            
            if not yield_data:
                continue
            
            # Check if yield is below threshold
            if yield_data.yield_pct < self.yield_threshold:
                severity = self._get_yield_severity(yield_data.yield_pct)
                
                alerts.append(Alert(
                    alert_type='LOW_YIELD',
                    severity=severity,
                    entity_type='BATCH_PAIR',
                    entity_id=f"{p02_batch}→{yield_data.p01_batch}",
                    batch=p02_batch,
                    material=yield_data.p01_material_code,
                    plant=1201,
                    metric_value=yield_data.yield_pct,
                    threshold=self.yield_threshold,
                    message=f"P02→P01 yield: {yield_data.yield_pct}% (Loss: {yield_data.loss_kg} KG) - {yield_data.p01_material_desc}",
                    detected_at=current_time
                ))
        
        return alerts
    
    def _get_yield_severity(self, yield_pct: float) -> str:
        """Determine alert severity based on yield percentage"""
        if yield_pct < 70:
            return 'CRITICAL'
        elif yield_pct < 80:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def detect_all_alerts(self) -> List[Alert]:
        """Run all alert detections"""
        alerts = []
        
        # Stuck in transit at Factory (1201)
        alerts.extend(self.detect_stuck_in_transit(plant=1201))
        
        # Low yield
        alerts.extend(self.detect_low_yield())
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
        alerts.sort(key=lambda x: severity_order.get(x.severity, 3))
        
        return alerts
    
    def alerts_to_dataframe(self, alerts: List[Alert]) -> pd.DataFrame:
        """Convert alerts to DataFrame"""
        if not alerts:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            'alert_type': a.alert_type,
            'severity': a.severity,
            'entity_type': a.entity_type,
            'entity_id': a.entity_id,
            'batch': a.batch,
            'material': a.material,
            'plant': a.plant,
            'metric_value': a.metric_value,
            'threshold': a.threshold,
            'message': a.message,
            'detected_at': a.detected_at
        } for a in alerts])
