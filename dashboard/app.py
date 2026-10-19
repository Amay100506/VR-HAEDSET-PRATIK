"""
NotifyIQ — Privacy-First, Explainable AI System for Android Notification Prioritization.
Streamlit Interactive Dashboard.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from backend.database.connection import init_db
from backend.database.repository import Repository
from backend.services.import_service import ImportService
from backend.utils.configuration import settings
from dashboard.charts import (
    build_category_distribution_chart,
    build_confusion_matrix_chart,
    build_priority_distribution_chart,
    build_priority_radar_chart,
    build_timeline_volume_chart,
)
from dashboard.components import render_category_badge, render_metric_card, render_priority_badge

# Page Configuration
st.set_page_config(
    page_title="NotifyIQ — Intelligent Notification Prioritization",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-weight: 600; }
    .stMetric { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 12px; }
    .reason-box {
        background-color: rgba(99, 102, 241, 0.08);
        border-left: 3px solid #6366F1;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Database & Repository
init_db()
repo = Repository()
import_service = ImportService(repository=repo)


def main():
    # Sidebar Navigation
    st.sidebar.image("https://img.icons8.com/fluency/96/appointment-reminders.png", width=48)
    st.sidebar.title("NotifyIQ")
    st.sidebar.caption("Explainable AI Notification Intelligence")
    
    pages = [
        "Overview",
        "Smart Inbox",
        "Notification Details",
        "Action Center",
        "Duplicate Center",
        "Analytics & Evaluation",
        "Settings & Privacy",
        "📱 Mobile App & Live Sync",
    ]
    selected_page = st.sidebar.radio("Navigation", pages, index=0)

    st.sidebar.divider()
    st.sidebar.caption("🔒 **Privacy Guarantee**: All processing and SQLite persistence remain strictly local on your machine. No notification text is transmitted to external clouds.")

    # -------------------------------------------------------------
    # PAGE 1: OVERVIEW
    # -------------------------------------------------------------
    if selected_page == "Overview":
        st.title("System Overview & Live Pulse")
        st.markdown("Real-time intelligence dashboard calculated from your captured notifications.")

        summary = repo.get_analytics_summary()
        if summary["total_notifications"] == 0:
            st.info("👋 Welcome to NotifyIQ! Your notification database is currently empty.")
            st.markdown(
                """
                To populate realistic notifications:
                1. Click below to run `python scripts/import_notifications.py --file data/sample_notifications.json`
                2. Or use the **Settings & Privacy** page to upload Android JSON export.
                """
            )
            if st.button("🚀 Load 50 Sample Notifications Now"):
                sample_file = BASE_DIR / "data" / "sample_notifications.json"
                if sample_file.exists():
                    from backend.ai.pipeline import AIPipeline
                    pipe = AIPipeline(repository=repo)
                    report = import_service.import_file(sample_file)
                    for ev in report.accepted_records:
                        pipe.process_notification(ev, persist=True)
                    st.success(f"Successfully processed and stored {report.accepted_count} sample notifications!")
                    st.rerun()
            return

        # KPI Metrics Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Total Captured", summary["total_notifications"], "Stored in local SQLite")
        with c2:
            render_metric_card("High Priority", summary["high_priority"], "Requires urgent attention", "#EF4444")
        with c3:
            render_metric_card("Actions Detected", summary["action_required"], "Tasks & requests detected", "#6366F1")
        with c4:
            render_metric_card("Duplicates Grouped", summary["duplicate_count"], "Identical & near alerts", "#10B981")

        st.divider()

        # Visual Charts
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("Priority Distribution")
            prio_data = repo.get_priority_counts()
            st.plotly_chart(build_priority_distribution_chart(prio_data), use_container_width=True)

        with col_right:
            st.subheader("Category Distribution")
            cat_data = repo.get_category_counts()
            st.plotly_chart(build_category_distribution_chart(cat_data), use_container_width=True)

        # Timeline Volume
        st.subheader("Notification Volume Over Time")
        timeline_data = repo.get_timeline_volume()
        st.plotly_chart(build_timeline_volume_chart(timeline_data), use_container_width=True)

        # Urgent Attention Section
        st.subheader("🚨 Highest Priority Notifications (Urgent)")
        high_items, _ = repo.list_notifications(priority_level="high", limit=5)
        if high_items:
            for item in high_items:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.02); border-left: 4px solid #EF4444; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <strong style="font-size: 1.05rem;">{item.get('title') or 'No Title'}</strong>
                                <span>{render_priority_badge(item['priority_level'], item['priority_score'])}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 6px;">
                                📱 <code>{item['package_name']}</code> | 🕒 {item['received_at'][:19].replace('T', ' ')}
                            </div>
                            <div style="font-size: 0.92rem; color: #E2E8F0; margin-bottom: 8px;">
                                {item.get('text') or ''}
                            </div>
                            <div style="font-size: 0.8rem; color: #CBD5E1;">
                                💡 <em>{'; '.join(item.get('priority_reasons', []))}</em>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.success("No high-priority alerts pending at this time.")

    # -------------------------------------------------------------
    # PAGE 2: SMART INBOX
    # -------------------------------------------------------------
    elif selected_page == "Smart Inbox":
        st.title("Smart Inbox")
        st.markdown("Searchable, explainable stream of incoming notifications.")

        # Filters Bar
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            search_query = st.text_input("🔍 Search notifications...", placeholder="Keyword, title, or package name")
        with f2:
            prio_filter = st.selectbox("Priority Level", ["All", "high", "medium", "low"])
        with f3:
            cat_filter = st.selectbox(
                "Category",
                ["All", "action_required", "transactional", "social", "promotional", "system", "unknown"],
            )
        with f4:
            action_only = st.checkbox("Has Action Only")

        # Query Database
        prio_param = None if prio_filter == "All" else prio_filter
        cat_param = None if cat_filter == "All" else cat_filter
        items, total_count = repo.list_notifications(
            search=search_query if search_query else None,
            priority_level=prio_param,
            category=cat_param,
            action_detected=True if action_only else None,
            limit=50,
        )

        st.caption(f"Showing **{len(items)}** of **{total_count}** matching notifications")

        if not items:
            st.info("No notifications match your current filter settings.")
        else:
            for item in items:
                with st.expander(
                    f"{'🔴' if item['priority_level']=='high' else ('🟡' if item['priority_level']=='medium' else '🟢')} "
                    f"[{item['priority_score']:.0f}] {item.get('title') or '(No Title)'} — {item['package_name']}"
                ):
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.markdown(f"**Content:** {item.get('text')}")
                        st.markdown(f"**Received:** `{item['received_at']}`")
                        if item.get("action_detected"):
                            st.info(f"⚡ **Action:** {item.get('action_text')} ({item.get('action_type')})")
                        if item.get("deadline_status") == "resolved":
                            st.warning(f"⏰ **Deadline:** {item.get('deadline_text')} → `{item.get('deadline_at')}`")
                        
                        st.markdown("**Explanation Reasons:**")
                        for r in item.get("priority_reasons", []):
                            st.markdown(f"<div class='reason-box'>• {r}</div>", unsafe_allow_html=True)

                    with col_b:
                        st.markdown(f"**Category:** {render_category_badge(item['category'])}", unsafe_allow_html=True)
                        st.markdown(f"**Confidence:** `{item['category_confidence']:.2f}` ({item['model_type']})")
                        st.markdown(f"**Priority Level:** `{item['priority_level'].upper()}` ({item['priority_score']:.1f}/100)")
                        if item.get("is_duplicate"):
                            st.markdown("🔁 *Grouped as duplicate alert*")

                        # Quick Action / Feedback
                        if st.button("Mark as Read", key=f"read_{item['id']}"):
                            repo.mark_notification_read(item['id'], True)
                            st.toast("Marked as read")

    # -------------------------------------------------------------
    # PAGE 3: NOTIFICATION DETAILS & EXPLAINABILITY
    # -------------------------------------------------------------
    elif selected_page == "Notification Details":
        st.title("Notification Deep Inspection & Feedback")
        st.markdown("Inspect priority score mechanics, component breakdown, and provide active feedback.")

        all_items, count = repo.list_notifications(limit=100)
        if not all_items:
            st.warning("No notifications available to inspect.")
            return

        options = {f"[{it['priority_score']:.0f}] {it.get('title') or it['package_name']} ({it['id'][:8]})": it['id'] for it in all_items}
        selected_label = st.selectbox("Select Notification to Inspect", list(options.keys()))
        selected_id = options[selected_label]
        item = repo.get_notification_by_id(selected_id)

        if item:
            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.subheader("Notification Metadata")
                st.write(f"**ID:** `{item['id']}`")
                st.write(f"**Event ID:** `{item['event_id']}`")
                st.write(f"**Source Package:** `{item['package_name']}`")
                st.write(f"**Received At:** `{item['received_at']}`")
                st.write(f"**Title:** {item.get('title')}")
                st.text_area("Permitted Content", value=item.get("text") or "", height=100, disabled=True)
                st.text_area("Normalized Classification Text", value=item.get("normalized_text") or "", height=70, disabled=True)

                st.subheader("Traceable AI Explanations")
                for r in item.get("priority_reasons", []):
                    st.markdown(f"<div class='reason-box'>🔍 {r}</div>", unsafe_allow_html=True)

            with col_right:
                st.subheader("Priority Formula Breakdown")
                st.caption("P = 0.30*U + 0.25*A + 0.25*D + 0.15*I + 0.05*R")
                breakdown = {
                    "urgency_score": item["urgency_score"],
                    "action_score": item["action_score"],
                    "deadline_score": item["deadline_score"],
                    "importance_score": item["importance_score"],
                    "recency_score": item["recency_score"],
                }
                st.plotly_chart(build_priority_radar_chart(breakdown), use_container_width=True)

                c_u, c_a, c_d, c_i, c_r = st.columns(5)
                c_u.metric("Urgency", f"{item['urgency_score']:.0f}")
                c_a.metric("Action", f"{item['action_score']:.0f}")
                c_d.metric("Deadline", f"{item['deadline_score']:.0f}")
                c_i.metric("Importance", f"{item['importance_score']:.0f}")
                c_r.metric("Recency", f"{item['recency_score']:.0f}")

            st.divider()

            # Active Learning Feedback Section
            st.subheader("✍️ Provide Human-in-the-Loop Feedback")
            st.caption("Correct any model prediction. Feedback is stored locally in SQLite to train future iterations.")
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                with st.form("feedback_category_form"):
                    st.write("**Correct Category Classification:**")
                    new_cat = st.selectbox(
                        "New Category",
                        ["action_required", "transactional", "social", "promotional", "system", "unknown"],
                        index=["action_required", "transactional", "social", "promotional", "system", "unknown"].index(item["category"]) if item["category"] in ["action_required", "transactional", "social", "promotional", "system", "unknown"] else 0,
                    )
                    submitted_cat = st.form_submit_button("Save Category Correction")
                    if submitted_cat:
                        repo.record_feedback(
                            notification_id=item["id"],
                            feedback_type="category",
                            original_value=item["category"],
                            corrected_value=new_cat,
                        )
                        st.success(f"Updated category from '{item['category']}' to '{new_cat}' and recorded feedback!")
                        st.rerun()

            with fcol2:
                with st.form("feedback_priority_form"):
                    st.write("**Adjust Priority Level:**")
                    new_prio = st.selectbox("Corrected Priority", ["high", "medium", "low"], index=["high", "medium", "low"].index(item["priority_level"]))
                    submitted_prio = st.form_submit_button("Save Priority Adjustment")
                    if submitted_prio:
                        repo.record_feedback(
                            notification_id=item["id"],
                            feedback_type="priority_level",
                            original_value=item["priority_level"],
                            corrected_value=new_prio,
                        )
                        st.success(f"Updated priority level to '{new_prio}' and recorded feedback!")
                        st.rerun()

    # -------------------------------------------------------------
    # PAGE 4: ACTION CENTER
    # -------------------------------------------------------------
    elif selected_page == "Action Center":
        st.title("Action Center")
        st.markdown("Track and manage actionable requests extracted from your notifications.")

        status_tab = st.radio("Status Filter", ["All", "open", "completed", "dismissed"], horizontal=True)
        status_filter = None if status_tab == "All" else status_tab
        actions = repo.list_actions(status=status_filter, limit=100)

        st.caption(f"Showing **{len(actions)}** actions")

        if not actions:
            st.info("No action items match the selected status.")
        else:
            for act in actions:
                with st.container():
                    col_act1, col_act2, col_act3 = st.columns([3, 1, 1])
                    with col_act1:
                        st.markdown(f"**⚡ {act['action_text']}**")
                        st.caption(f"App: <code>{act['package_name']}</code> | Type: `{act['action_type']}` | Ref: *{act.get('notification_title') or 'Notification'}*", unsafe_allow_html=True)
                        if act.get("deadline_at"):
                            st.warning(f"⏰ Deadline: `{act['deadline_at'][:19].replace('T', ' ')}`")

                    with col_act2:
                        st.markdown(f"Status: **`{act['status'].upper()}`**")

                    with col_act3:
                        if act["status"] == "open":
                            if st.button("Complete", key=f"comp_{act['id']}"):
                                repo.update_action_status(act["id"], "completed")
                                st.rerun()
                            if st.button("Dismiss", key=f"dism_{act['id']}"):
                                repo.update_action_status(act["id"], "dismissed")
                                st.rerun()
                        else:
                            if st.button("Reopen", key=f"reopen_{act['id']}"):
                                repo.update_action_status(act["id"], "open")
                                st.rerun()
                    st.divider()

    # -------------------------------------------------------------
    # PAGE 5: DUPLICATE CENTER
    # -------------------------------------------------------------
    elif selected_page == "Duplicate Center":
        st.title("Duplicate Grouping Center")
        st.markdown("Inspect duplicate groups formed via exact fingerprinting and conservative similarity.")

        groups = repo.list_duplicate_groups()
        if not groups:
            st.info("No repeated or duplicate notification groups found.")
        else:
            st.success(f"Identified **{len(groups)}** duplicate clusters.")
            for g in groups:
                with st.expander(f"🔁 Cluster `{g['id'][:8]}` — {g['group_size']} notifications (Method: {g['group_method'] if 'group_method' in g else g.get('grouping_method')})"):
                    st.write(f"**Representative Sample:** {g.get('sample_title')}")
                    st.write(f"**Fingerprint:** `{g['fingerprint']}`")
                    members = repo.get_group_members(g["id"])
                    st.markdown("**Cluster Members:**")
                    for m in members:
                        st.markdown(f"- 🕒 `{m['received_at'][:19]}` | **{m.get('title')}**: {m.get('text')} *(Event: `{m['event_id']}`)*")

    # -------------------------------------------------------------
    # PAGE 6: ANALYTICS & MODEL EVALUATION
    # -------------------------------------------------------------
    elif selected_page == "Analytics & Evaluation":
        st.title("Analytics & AI Model Evaluation")
        tab_ops, tab_eval = st.tabs(["📊 Operational Analytics", "🔬 Model Evaluation & Benchmarks"])

        with tab_ops:
            st.subheader("Application-Level Volume Breakdown")
            app_data = repo.get_app_distribution()
            if app_data:
                app_df = pd.DataFrame(app_data)
                st.dataframe(app_df, use_container_width=True)
            else:
                st.info("No application distribution data available.")

        with tab_eval:
            st.subheader("Held-Out Test Set Performance")
            report_file = settings.evaluation_report_path
            if not report_file.exists():
                st.warning("Model evaluation report not found. Run `python scripts/evaluate_model.py` to evaluate.")
            else:
                with open(report_file, "r", encoding="utf-8") as f:
                    eval_data = json.load(f)

                cat_m = eval_data["category_classification"]
                base_c = eval_data["baseline_comparison"]
                high_p = eval_data["high_priority_detection"]
                lat_m = eval_data["latency_ms"]

                # Benchmark Cards
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Category Accuracy", f"{cat_m['accuracy'] * 100:.1f}%")
                m2.metric("NotifyIQ Macro-F1", f"{cat_m['macro_f1']:.3f}", delta=f"+{base_c['macro_f1_improvement']:.3f} vs Baseline")
                m3.metric("High-Priority Precision", f"{high_p['precision'] * 100:.1f}%")
                m4.metric("Median Latency", f"{lat_m['median']:.1f} ms")

                st.divider()

                col_cm, col_perclass = st.columns([1, 1])
                with col_cm:
                    st.subheader("Confusion Matrix")
                    st.plotly_chart(
                        build_confusion_matrix_chart(cat_m["confusion_matrix"], cat_m["labels"]),
                        use_container_width=True,
                    )

                with col_perclass:
                    st.subheader("Per-Class Metrics")
                    per_class_df = pd.DataFrame.from_dict(cat_m["per_class"], orient="index")
                    st.dataframe(per_class_df.style.format("{:.2f}"), use_container_width=True)

                st.info(
                    "📌 **Evaluation Methodology Note**: Metrics were calculated on a held-out synthetic test set "
                    "(126 samples, distinct seed) comparing the scikit-learn TF-IDF + Logistic Regression model "
                    "against a deterministic rules-only baseline."
                )

    # -------------------------------------------------------------
    # PAGE 7: SETTINGS & PRIVACY
    # -------------------------------------------------------------
    elif selected_page == "Settings & Privacy":
        st.title("Settings & Privacy Controls")
        st.markdown("NotifyIQ is designed privacy-first. You retain complete control over storage and retention.")

        st.subheader("🛡️ Privacy Policy & Security Guarantee")
        st.markdown(
            """
            - **Local Processing**: Ingestion, classification, scoring, and SQLite persistence run 100% locally on your machine.
            - **Zero Cloud APIs**: No notification text is ever dispatched to OpenAI, Anthropic, Google Cloud, or third-party cloud LLMs.
            - **No Raw Text in Logs**: Application logs only record event IDs and operational metrics.
            - **Local-Only API**: Default binds strictly to `127.0.0.1` (loopback interface).
            """
        )

        st.divider()

        st.subheader("Data Export")
        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            json_export = import_service.export_notifications_json()
            st.download_button(
                "📥 Export Processed Notifications (JSON)",
                data=json_export,
                file_name="notifyiq_export.json",
                mime="application/json",
            )
        with c_exp2:
            csv_export = import_service.export_notifications_csv()
            st.download_button(
                "📥 Export Processed Notifications (CSV)",
                data=csv_export,
                file_name="notifyiq_export.csv",
                mime="text/csv",
            )

        st.divider()

        st.subheader("Purge & Delete Data")
        st.warning("Permanently wipe all captured notifications, actions, and feedback from the local database.")
        confirm_purge = st.checkbox("I confirm that I want to delete all stored notification records")
        if st.button("🗑️ Purge All Stored Data", type="primary", disabled=not confirm_purge):
            summary = repo.purge_all_data()
            st.success(f"Purge complete: Deleted {summary['deleted_notifications']} notifications and {summary['deleted_actions']} actions.")
            st.rerun()

    # -------------------------------------------------------------
    # PAGE 8: MOBILE APP & REAL-TIME SYNC
    # -------------------------------------------------------------
    elif selected_page == "📱 Mobile App & Live Sync":
        st.title("📱 Real-Time Mobile Companion App")
        st.markdown(
            "Download and install NotifyIQ onto your mobile device as a Progressive Web App (PWA) "
            "with live WebSocket push notifications and local offline caching."
        )

        import io
        import socket
        import qrcode

        def get_lan_ip() -> str:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

        lan_ip = get_lan_ip()
        mobile_url = f"http://{lan_ip}:8000/mobile"

        col_qr, col_info = st.columns([1, 1.4])
        with col_qr:
            st.subheader("Scan with Your Phone Camera")
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(mobile_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#4F46E5", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Scan to open on phone: {mobile_url}", width=260)

        with col_info:
            st.subheader("How to Install as a Mobile App")
            st.markdown(
                f"""
                1. Make sure your phone is connected to the **same Wi-Fi network**.
                2. Scan the QR code or open:  
                   👉 **[{mobile_url}]({mobile_url})**
                3. **Install to Home Screen**:
                   - **Android (Chrome)**: Tap the banner **"Install Now"** or tap `⋮` (menu) $\rightarrow$ **"Install App"** / **"Add to Home Screen"**.
                   - **iOS (Safari)**: Tap the Share icon $\rightarrow$ **"Add to Home Screen"**.
                4. The NotifyIQ app icon will appear directly on your phone's home screen and launch in full-screen native mode!
                """
            )

            st.divider()

            # Live Test Trigger
            st.subheader("⚡ Send Live Real-Time Test Alert to Phone")
            st.caption("Broadcasts an urgent high-priority notification to all connected mobile devices in real time over WebSocket.")
            
            test_app = st.selectbox("Simulated App", ["Chase Banking", "Gmail Work", "Slack Team Sync", "Amazon Shopping"])
            test_title = st.text_input("Alert Title", value="Action Required: Confirm Identity Verification")
            test_text = st.text_input("Alert Body", value="Please complete your verification within 24 hours to prevent account freeze.")

            if st.button("🚀 Push Live Alert to Mobile Now"):
                import requests
                try:
                    res = requests.post(
                        "http://127.0.0.1:8000/notifications/process",
                        json={
                            "notification": {
                                "schema_version": 1,
                                "event_id": f"live-test-{datetime.now().timestamp()}",
                                "package_name": "com.bank.secure" if "Bank" in test_app else "com.work.app",
                                "title": test_title,
                                "text": test_text,
                                "posted_at": datetime.now(timezone.utc).isoformat(),
                                "event_type": "posted",
                            },
                            "persist": True,
                        },
                        timeout=5,
                    )
                    if res.status_code == 200:
                        st.success("✅ Broadcasted live notification! Check your phone screen.")
                    else:
                        st.error(f"Failed to broadcast: {res.text}")
                except Exception as ex:
                    st.error(f"Error reaching API gateway: {ex}")


if __name__ == "__main__":
    main()
