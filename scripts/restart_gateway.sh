#!/bin/bash
# Restart hermes-gateway so it loads the rebuilt pipx venv (python3.11/0.19.0)
# instead of the deleted python3.14 venv the current process is running from.
systemctl --user restart hermes-gateway
