{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "bitcoin-price.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Create labels used in the chart.
*/}}
{{- define "bitcoin-price.labels" -}}
app.kubernetes.io/name: {{ include "bitcoin-price.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
