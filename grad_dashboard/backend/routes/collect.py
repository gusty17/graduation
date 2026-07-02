from flask import Blueprint, request, jsonify

import services.collector_service as collector

collect_bp = Blueprint("collect", __name__)


@collect_bp.route("/collect/sessions")
def sessions():
    """Existing sessions (+ which labels each already has) and a suggested next
    session name, so the UI can prefill the form and warn on overwrite."""
    return jsonify({
        "sessions": collector.sessions_detail(),
        "suggested": collector.suggest_next_session(),
        "labels": list(collector.LABELS),
        "default_duration": 600,
    })


@collect_bp.route("/collect/start", methods=["POST"])
def start():
    """Begin recording. Body: {label: "0p"|"1p"|"2p", session?: str, duration?: seconds}."""
    data = request.get_json(silent=True) or {}
    label = data.get("label")
    session = data.get("session") or collector.suggest_next_session()
    duration = data.get("duration", 600)
    try:
        return jsonify(collector.start_collection(label, session, duration))
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 400


@collect_bp.route("/collect/stop", methods=["POST"])
def stop():
    """Stop the active recording early and finalize the file."""
    summary = collector.stop_collection(reason="manual")
    if summary is None:
        return jsonify({"error": "no active collection"}), 400
    return jsonify({"summary": summary})


@collect_bp.route("/collect/status")
def status():
    """Live status: countdown + per-receiver row counts, polled by the UI."""
    return jsonify(collector.status())
