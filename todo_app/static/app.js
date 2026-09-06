const taskListEl = document.getElementById("task-list");
const addTaskForm = document.querySelector(".add-task-form");
const newTaskInput = document.getElementById("new-task");

function renderTasks(tasks) {
    taskListEl.innerHTML = "";
    for (const task of tasks) {
        const itemEl = document.createElement("li");

        const checkboxEl = document.createElement("input");
        checkboxEl.type = "checkbox";
        checkboxEl.name = `task-${task.id}`;
        checkboxEl.id = `task-${task.id}`;
        checkboxEl.checked = task.done;
        checkboxEl.addEventListener("change", async function(){
            const response = await fetch(`/api/tasks/${task.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({done: checkboxEl.checked})
            });
            if (!response.ok) {
                alert("ส่งข้อมูลล้มเหลว");
                return;
            }
            task.done = checkboxEl.checked;
            updateTaskCount(tasks);
        });

        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.textContent = "Delete";
        deleteBtn.className = "delete-btn";
        deleteBtn.addEventListener("click" , async function(){
            const response = await fetch(`/api/tasks/${task.id}`, {method: 'DELETE'})
            if (!response.ok) {
                alert("ส่งข้อมูลล้มเหลว");
                return;
            }
            loadTasks();
        } );


        const labelEl = document.createElement("label");
        labelEl.htmlFor = `task-${task.id}`;
        labelEl.textContent = task.detail;

        itemEl.appendChild(checkboxEl);
        itemEl.appendChild(labelEl);
        itemEl.appendChild(deleteBtn);
        taskListEl.appendChild(itemEl);
    }
    updateTaskCount(tasks);
}

async function loadTasks() {
    const response = await fetch('/api/tasks');
    if (!response.ok) {
        if (response.status === 401) {
            window.location.href = '/';
            return;
        }
        alert("โหลดข้อมูลไม่สำเร็จ");
        return;
    }
    const tasks = await response.json();
    renderTasks(tasks);
}

async function handleAddTask(event) {
    event.preventDefault();
    const detail = newTaskInput.value.trim();
    if (detail === "") {
        newTaskInput.value = "";
        return;
    }
    
    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({detail: detail})
    });

    if (!response.ok) {
        alert("ส่งข้อมูลล้มเหลว");
        return;
    }

    newTaskInput.value = "";
    loadTasks();
}

function updateTaskCount(tasks) {
    let taskCount = tasks.filter(t => t.done === false).length;
    document.getElementById("task-count").textContent = "เหลืออีก " + taskCount + " งาน";
}

loadTasks();
addTaskForm.addEventListener("submit", handleAddTask);
