{{/*
Expand the name of the chart.
*/}}
{{- define "kagent-memory.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "kagent-memory.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "kagent-memory.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kagent-memory.labels" -}}
helm.sh/chart: {{ include "kagent-memory.chart" . }}
{{ include "kagent-memory.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kagent-memory.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kagent-memory.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kagent-memory.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kagent-memory.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get Qdrant URL - either from values or auto-compute from embedded chart
*/}}
{{- define "kagent-memory.qdrantUrl" -}}
{{- if .Values.memory.qdrant.url }}
{{- .Values.memory.qdrant.url }}
{{- else if .Values.qdrant.enabled }}
{{- printf "http://%s-qdrant:6333" .Release.Name }}
{{- else }}
{{- fail "memory.qdrant.url must be set when qdrant.enabled is false" }}
{{- end }}
{{- end }}

{{/*
Get the secret name for OpenAI API key
*/}}
{{- define "kagent-memory.openaiSecretName" -}}
{{- if .Values.openai.existingSecret }}
{{- .Values.openai.existingSecret }}
{{- else }}
{{- include "kagent-memory.fullname" . }}
{{- end }}
{{- end }}
