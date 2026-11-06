#!/usr/bin/env bash
# Lab 6 준비 — data/voc_tickets.csv를 내 Google Cloud 프로젝트의 BigQuery에 올립니다.
# 실습용 가상 데이터. lab.env의 PROJECT_ID를 내 프로젝트로 바꾼 뒤 실행하세요:  bash setup/load_to_bigquery.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
# 변수는 프로젝트 맨 위의 lab.env 한 곳에서만 바꿉니다 (PROJECT_ID · BQ_DATASET · BQ_LOCATION · BQ_TABLE)
source "$HERE/lab.env"
DATASET="$BQ_DATASET"; LOCATION="$BQ_LOCATION"; TABLE="$BQ_TABLE"
SCHEMA="ticket_id:STRING,created_at:DATETIME,week_start:DATE,channel:STRING,product:STRING,category:STRING,severity:STRING,status:STRING,region:STRING,customer_name:STRING,phone:STRING,message:STRING,resolution_hours:FLOAT,csat:INTEGER"

bq --project_id="$PROJECT_ID" show --dataset "$PROJECT_ID:$DATASET" >/dev/null 2>&1 || \
  bq --project_id="$PROJECT_ID" --location="$LOCATION" mk --dataset --description "Cymbal VOC (실습용 가상 데이터)" "$PROJECT_ID:$DATASET"
bq --project_id="$PROJECT_ID" --location="$LOCATION" load --replace --source_format=CSV --skip_leading_rows=1 \
  "$PROJECT_ID:$DATASET.$TABLE" "$HERE/data/voc_tickets.csv" "$SCHEMA"
bq --project_id="$PROJECT_ID" query --use_legacy_sql=false \
  "SELECT week_start, COUNT(*) AS tickets FROM \`$PROJECT_ID.$DATASET.$TABLE\` GROUP BY week_start ORDER BY week_start"
echo "완료: $PROJECT_ID.$DATASET.$TABLE"
