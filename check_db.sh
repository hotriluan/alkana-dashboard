#!/bin/bash
docker ps
echo "---"
docker ps --format '{{.Names}}' | grep -E 'db|postgres'
