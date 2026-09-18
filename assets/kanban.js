export default function(component) {
    const {
        parentElement,
        data,
        setTriggerValue
    } = component;

    const root = parentElement.querySelector("#kanban-root");

    if (!root) {
        return;
    }

    root.replaceChildren();

    const tasks = data?.tasks ?? [];
    const statuses = data?.statuses ?? [];
    const priorityColors = data?.priority_colors ?? {};
    const personColors = data?.person_colors ?? {};
    const statusColors = data?.status_colors ?? {};

    const board = document.createElement("div");
    board.className = "kb-board";

    function makeBadge(text, color) {
        const el = document.createElement("span");
        el.className = "kb-badge";
        el.textContent = text ?? "—";
        el.style.backgroundColor = color ?? "#666";
        return el;
    }

    statuses.forEach((status) => {
        const column = document.createElement("section");
        column.className = "kb-column";
        column.dataset.status = status;

        const header = document.createElement("div");
        header.className = "kb-column-header";

        const title = document.createElement("div");
        title.className = "kb-column-title";
        title.textContent = status;

        const statusTasks = tasks.filter(
            (task) => task.status === status
        );

        const count = document.createElement("span");
        count.className = "kb-count";
        count.textContent = String(statusTasks.length);

        header.appendChild(title);
        header.appendChild(count);

        const cards = document.createElement("div");
        cards.className = "kb-cards";

        column.addEventListener("dragover", (event) => {
            event.preventDefault();
            column.classList.add("drag-over");
        });

        column.addEventListener("dragleave", (event) => {
            if (!column.contains(event.relatedTarget)) {
                column.classList.remove("drag-over");
            }
        });

        column.addEventListener("drop", (event) => {
            event.preventDefault();
            column.classList.remove("drag-over");

            const rawId = event.dataTransfer.getData("text/task-id");

            if (!rawId) {
                return;
            }

            const taskId = Number(rawId);

            const task = tasks.find(
                (item) => Number(item.id) === taskId
            );

            if (!task || task.status === status) {
                return;
            }

            setTriggerValue(
                "move",
                {
                    task_id: taskId,
                    status: status
                }
            );
        });

        if (statusTasks.length === 0) {
            const empty = document.createElement("div");
            empty.className = "kb-empty";
            empty.textContent = "Geen taken";
            cards.appendChild(empty);
        }

        statusTasks.forEach((task) => {
            const card = document.createElement("article");
            card.className = "kb-card";
            card.draggable = true;
            card.dataset.taskId = String(task.id);

            card.addEventListener("dragstart", (event) => {
                card.classList.add("dragging");
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData(
                    "text/task-id",
                    String(task.id)
                );
            });

            card.addEventListener("dragend", () => {
                card.classList.remove("dragging");

                parentElement
                    .querySelectorAll(".kb-column")
                    .forEach((el) => {
                        el.classList.remove("drag-over");
                    });
            });

            const taskTitle = document.createElement("div");
            taskTitle.className = "kb-title";
            taskTitle.textContent = task.title ?? "";

            const footer = document.createElement("div");
            footer.className = "kb-footer";

            footer.appendChild(
                makeBadge(
                    task.priority ?? "—",
                    priorityColors[task.priority] ?? "#666"
                )
            );

            footer.appendChild(
                makeBadge(
                    task.person ?? "—",
                    personColors[task.person] ?? "#666"
                )
            );

            if (
                task.sprint &&
                task.sprint !== "Niet van toepassing"
            ) {
                const sprintBadge = makeBadge(
                    task.sprint,
                    "#7E57C2"
                );

                sprintBadge.classList.add("kb-sprint");
                footer.appendChild(sprintBadge);
            }

            footer.appendChild(
                makeBadge(
                    task.status ?? "—",
                    statusColors[task.status] ?? "#666"
                )
            );

            const info = document.createElement("button");
            info.className = "kb-info";
            info.type = "button";
            info.textContent = "ℹ Info";
            info.draggable = false;

            info.addEventListener("pointerdown", (event) => {
                event.stopPropagation();
            });

            info.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();

                setTriggerValue(
                    "info",
                    Number(task.id)
                );
            });

            footer.appendChild(info);

            card.appendChild(taskTitle);
            card.appendChild(footer);

            cards.appendChild(card);
        });

        column.appendChild(header);
        column.appendChild(cards);
        board.appendChild(column);
    });

    root.appendChild(board);
}
