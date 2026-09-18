from pathlib import Path
from datetime import date

import streamlit as st
from supabase import create_client, Client


# ============================================================
# PATHS / ASSETS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

APP_CSS = (BASE_DIR / "styles.css").read_text(encoding="utf-8")
KANBAN_HTML = (ASSETS_DIR / "kanban.html").read_text(encoding="utf-8")
KANBAN_CSS = (ASSETS_DIR / "kanban.css").read_text(encoding="utf-8")
KANBAN_JS = (ASSETS_DIR / "kanban.js").read_text(encoding="utf-8")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Digital Twin Kanban",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


# ============================================================
# CONFIG
# ============================================================

PEOPLE = ["Phong", "Joris", "Ruzz", "Tijn"]
EVERYONE = "iedereen"

PRIORITIES = ["Hoog", "medium", "laag"]

STATUSES = [
    "Niet gestart",
    "In uitvoering",
    "In review",
    "Klaar",
]

SPRINTS = [
    "Niet van toepassing",
    "Sprint 1",
    "Sprint 2",
    "Sprint 3",
    "Sprint 4",
    "Sprint 5",
    "Sprint 6",
    "Sprint 7",
    "Sprint 8",
]

PERSON_COLORS = {
    "Phong": "#4285F4",
    "Joris": "#E53935",
    "Ruzz": "#8BC34A",
    "Tijn": "#7E57C2",
    "iedereen": "#F57C00",
}

PRIORITY_COLORS = {
    "Hoog": "#D50000",
    "medium": "#F9A825",
    "laag": "#43A047",
}

STATUS_COLORS = {
    "Niet gestart": "#9E9E9E",
    "In uitvoering": "#42A5F5",
    "In review": "#AB47BC",
    "Klaar": "#43A047",
}


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = get_supabase()


def fetch_tasks():
    result = (
        supabase
        .table("tasks")
        .select("*")
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


def create_task(
    title,
    priority,
    person,
    new_sprint,
    status,
    deadline,
    description,
):
    payload = {
        "title": title.strip(),
        "priority": priority,
        "person": person,
        "sprint": new_sprint,
        "status": status,
        "deadline": deadline.isoformat() if deadline else None,
        "description": description.strip() if description else None,
    }

    supabase.table("tasks").insert(payload).execute()


def update_task(
    task_id,
    title,
    priority,
    person,
    sprint,
    status,
    deadline,
    description,
):
    payload = {
        "title": title.strip(),
        "priority": priority,
        "person": person,
        "sprint": sprint,
        "status": status,
        "deadline": deadline.isoformat() if deadline else None,
        "description": description.strip() if description else None,
    }

    (
        supabase
        .table("tasks")
        .update(payload)
        .eq("id", task_id)
        .execute()
    )


def update_task_status(task_id, status):
    (
        supabase
        .table("tasks")
        .update({"status": status})
        .eq("id", task_id)
        .execute()
    )


def delete_task(task_id):
    (
        supabase
        .table("tasks")
        .delete()
        .eq("id", task_id)
        .execute()
    )


# ============================================================
# SESSION STATE HELPERS
# ============================================================

def close_all_dialogs():
    st.session_state.pop("info_task_id", None)
    st.session_state.pop("delete_task_id", None)


def close_dialogs_on_change():
    close_all_dialogs()


# ============================================================
# CUSTOM DRAG & DROP KANBAN
# ============================================================

kanban_component = st.components.v2.component(
    name="digital_twin_drag_kanban",
    html=KANBAN_HTML,
    css=KANBAN_CSS,
    js=KANBAN_JS,
    isolate_styles=True,
)


# ============================================================
# DIALOGS
# ============================================================

@st.dialog(
    "Taakinfo",
    width="large",
    on_dismiss=close_all_dialogs,
)
def task_info_dialog(task):
    current_deadline = task.get("deadline")
    parsed_deadline = None

    if current_deadline:
        try:
            parsed_deadline = date.fromisoformat(current_deadline)
        except Exception:
            parsed_deadline = None

    st.markdown(f"### {task.get('title', '')}")

    with st.form(f"task_info_form_{task['id']}"):
        title = st.text_input(
            "Taak",
            value=task.get("title", ""),
        )

        c1, c2, c3 = st.columns(3)

        priority = c1.selectbox(
            "Prioriteit",
            PRIORITIES,
            index=(
                PRIORITIES.index(task.get("priority"))
                if task.get("priority") in PRIORITIES
                else 0
            ),
        )

        person_options = PEOPLE + [EVERYONE]

        person = c2.selectbox(
            "Persoon",
            person_options,
            index=(
                person_options.index(task.get("person"))
                if task.get("person") in person_options
                else 0
            ),
        )

        status = c3.selectbox(
            "Status",
            STATUSES,
            index=(
                STATUSES.index(task.get("status"))
                if task.get("status") in STATUSES
                else 0
            ),
        )

        use_deadline = st.checkbox(
            "Deadline gebruiken",
            value=parsed_deadline is not None,
        )

        deadline = st.date_input(
            "Deadline",
            value=parsed_deadline or date.today(),
            disabled=not use_deadline,
        )

        current_sprint = task.get("sprint") or "Niet van toepassing"

        sprint = st.selectbox(
            "Sprint",
            SPRINTS,
            index=SPRINTS.index(current_sprint)
            if current_sprint in SPRINTS
            else 0,
            key=f"edit_sprint_{task['id']}",
        )

        description = st.text_area(
            "Omschrijving",
            value=task.get("description") or "",
            height=150,
        )

        save = st.form_submit_button(
            "💾 Opslaan",
            type="primary",
            use_container_width=True,
        )

        if save:
            if not title.strip():
                st.error("Geef de taak een naam.")
            else:
                update_task(
                    task["id"],
                    title,
                    priority,
                    person,
                    sprint,
                    status,
                    deadline if use_deadline else None,
                    description,
                )
                close_all_dialogs()
                st.rerun()

    st.divider()

    close_col, delete_col = st.columns(2)

    if close_col.button(
        "Sluiten",
        use_container_width=True,
        key=f"close_info_{task['id']}",
    ):
        close_all_dialogs()
        st.rerun()

    if delete_col.button(
        "🗑️ Verwijderen",
        use_container_width=True,
        key=f"open_delete_{task['id']}",
    ):
        # Sluit info-dialog en open daarna pas de delete-dialog.
        st.session_state.pop("info_task_id", None)
        st.session_state["delete_task_id"] = int(task["id"])
        st.rerun()


@st.dialog(
    "Taak verwijderen",
    width="small",
    on_dismiss=close_all_dialogs,
)
def delete_task_dialog(task):
    st.warning(
        f'Weet je zeker dat je **"{task["title"]}"** definitief wilt verwijderen?'
    )

    st.caption("Deze actie kan niet ongedaan worden gemaakt.")

    confirm_col, cancel_col = st.columns(2)

    if confirm_col.button(
        "Ja, definitief verwijderen",
        type="primary",
        use_container_width=True,
        key=f"confirm_delete_{task['id']}",
    ):
        delete_task(task["id"])
        close_all_dialogs()
        st.rerun()

    if cancel_col.button(
        "Annuleren",
        use_container_width=True,
        key=f"cancel_delete_{task['id']}",
    ):
        close_all_dialogs()
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("🫁 Digital Twin Kanban")

st.caption(
    "Eén gedeeld bord voor het hele team. "
    "Sleep taken tussen kolommen of klik op Info."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Weergave")

    current_user = st.selectbox(
        "Wie ben je?",
        PEOPLE,
        index=0,
        key="current_user",
        on_change=close_dialogs_on_change,
    )

    view_mode = st.radio(
        "Bord",
        ["Main board", "Mijn taken"],
        index=0,
        key="view_mode",
        on_change=close_dialogs_on_change,
    )

    st.subheader("Filters")

    filter_priority = st.multiselect(
        "Prioriteit",
        PRIORITIES,
        default=[],
        key="filter_priority",
        on_change=close_dialogs_on_change,
    )

    sprint_filter = st.multiselect(
        "Sprint",
        SPRINTS,
        placeholder="Choose options",
    )

    filter_status = st.multiselect(
        "Status",
        STATUSES,
        default=[],
        key="filter_status",
        on_change=close_dialogs_on_change,
    )

    st.divider()

    st.subheader("➕ Nieuwe taak")

    with st.form(
        "new_task_form",
        clear_on_submit=True,
    ):
        title = st.text_input("Taak")

        priority = st.selectbox(
            "Prioriteit",
            PRIORITIES,
        )

        person_options = PEOPLE + [EVERYONE]

        person = st.selectbox(
            "Persoon",
            person_options,
            index=person_options.index(current_user),
        )

        new_sprint = st.selectbox(
            "Sprint",
            SPRINTS,
            index=0,
            key="new_sprint",
        )

        status = st.selectbox(
            "Status",
            STATUSES,
        )

        use_deadline = st.checkbox(
            "Deadline gebruiken",
            value=True,
        )

        deadline = st.date_input(
            "Deadline",
            value=date.today(),
            disabled=not use_deadline,
        )

        description = st.text_area(
            "Omschrijving",
            height=95,
        )

        submitted = st.form_submit_button(
            "Taak toevoegen",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not title.strip():
                st.error("Geef de taak een naam.")
            else:
                create_task(
                    title,
                    priority,
                    person,
                    sprint,
                    status,
                    deadline if use_deadline else None,
                    description,
                )
                st.rerun()


# ============================================================
# LOAD TASKS
# ============================================================

all_tasks = fetch_tasks()
tasks = list(all_tasks)

task_lookup = {
    int(task["id"]): task
    for task in all_tasks
}


# ============================================================
# OPEN DIALOGS
# ============================================================

# Belangrijk: precies één dialog tegelijk.
delete_task_id = st.session_state.get("delete_task_id")
info_task_id = st.session_state.get("info_task_id")

if delete_task_id is not None:
    task_to_delete = task_lookup.get(int(delete_task_id))

    if task_to_delete:
        delete_task_dialog(task_to_delete)
    else:
        st.session_state.pop("delete_task_id", None)

elif info_task_id is not None:
    selected_task = task_lookup.get(int(info_task_id))

    if selected_task:
        task_info_dialog(selected_task)
    else:
        st.session_state.pop("info_task_id", None)


# ============================================================
# VIEW / FILTERS
# ============================================================

if view_mode == "Mijn taken":
    tasks = [
        task
        for task in tasks
        if task.get("person") in (current_user, EVERYONE)
    ]

if filter_priority:
    tasks = [
        task
        for task in tasks
        if task.get("priority") in filter_priority
    ]

if filter_status:
    tasks = [
        task
        for task in tasks
        if task.get("status") in filter_status
    ]

if sprint_filter:
    tasks = [
        task
        for task in tasks
        if (task.get("sprint") or "Niet van toepassing") in sprint_filter
    ]


# ============================================================
# SUMMARY
# ============================================================

metrics = st.columns(5)

metrics[0].metric(
    "Totaal",
    len(tasks),
)

for index, status in enumerate(
    STATUSES,
    start=1,
):
    metrics[index].metric(
        status,
        sum(
            task.get("status") == status
            for task in tasks
        ),
    )

st.divider()


# ============================================================
# BOARD HEIGHT
# ============================================================

max_in_column = max(
    [
        sum(
            task.get("status") == status
            for task in tasks
        )
        for status in STATUSES
    ]
    or [0]
)

board_height = max(
    350,
    min(
        1000,
        90 + (max_in_column * 92),
    ),
)


# ============================================================
# RENDER BOARD
# ============================================================

result = kanban_component(
    data={
        "tasks": tasks,
        "statuses": STATUSES,
        "priority_colors": PRIORITY_COLORS,
        "person_colors": PERSON_COLORS,
        "status_colors": STATUS_COLORS,
    },
    default={},
    on_move_change=lambda: None,
    on_info_change=lambda: None,
    key="digital_twin_board",
    width="stretch",
    height=board_height,
)


# ============================================================
# PROCESS DRAG & DROP
# ============================================================

if result.move:
    move = result.move

    task_id = int(move["task_id"])
    new_status = move["status"]

    if new_status in STATUSES:
        update_task_status(
            task_id,
            new_status,
        )

    st.rerun()


# ============================================================
# PROCESS INFO BUTTON
# ============================================================

if result.info:
    # Een info-event mag nooit tegelijk met een delete-dialog actief zijn.
    st.session_state.pop("delete_task_id", None)
    st.session_state["info_task_id"] = int(result.info)
    st.rerun()
