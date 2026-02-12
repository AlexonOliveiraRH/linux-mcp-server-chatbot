#!/bin/bash
#Run inferences

# Set INGRESS_HOST and INGRESS_PORT only if they are not already set.
export INGRESS_HOST=${INGRESS_HOST:-localhost}
export INGRESS_PORT=${INGRESS_PORT:-8080}

echo "➡️ Using INGRESS_HOST=${INGRESS_HOST} and INGRESS_PORT=${INGRESS_PORT}"

# Get required service names and hostnames
INGRESS_GATEWAY_SERVICE=$(kubectl get svc -n istio-system -l app=istio-ingressgateway -o jsonpath='{.items[0].metadata.name}{"\n"}')
export SERVICE_HOSTNAME=$(kubectl get inferenceservice gemma-3-270m -o jsonpath='{.status.url}' | cut -d "/" -f 3)

# --- NEW: Check if port-forward is already running ---
PF_COMMAND_PATTERN="kubectl port-forward --namespace istio-system svc/${INGRESS_GATEWAY_SERVICE} ${INGRESS_PORT}:80"

if pgrep -f "${PF_COMMAND_PATTERN}" > /dev/null; then
    echo "✅ Port-forward process already detected. Proceeding."
else
    echo "➡️ Starting port-forward..."
    # Start port-forward in the background so the script can continue
    ${PF_COMMAND_PATTERN} &
    PORT_FORWARD_PID=$!

    # Set up a trap to kill the port-forward process ONLY if this script started it.
    #trap "echo '➡️ Stopping port-forward process (PID: $PORT_FORWARD_PID)...'; kill $PORT_FORWARD_PID" EXIT

    # Wait a moment for the connection to be established
    #sleep 2
fi
# ----------------------------------------------------
