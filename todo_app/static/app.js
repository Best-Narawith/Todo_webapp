const taskListEl = document.getElementById("task-list");
const addTaskForm = document.querySelector(".add-task-form");
const newTaskInput = document.getElementById("new-task");
const addTaskBtn = document.getElementById("add-task-btn");

function renderTasks(tasks) {
    taskListEl.innerHTML = "";
    addTaskBtn.disabled = false;
    if (tasks.length === 0) {
        const itemEl = document.createElement("li");
        itemEl.textContent = "ยังไม่มีงาน";
        taskListEl.appendChild(itemEl);
        updateTaskCount(tasks);
        return;
    }
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
            const error = await failureMessage(response, "ส่งข้อมูลล้มเหลว");
            if (error) {
                await loadTasks();
                showError(error);
                return;
            }
            hideError();
            task.done = checkboxEl.checked;
            updateTaskCount(tasks);
        });

        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.textContent = "Delete";
        deleteBtn.className = "delete-btn";
        deleteBtn.addEventListener("click" , async function(){
            const response = await fetch(`/api/tasks/${task.id}`, {method: 'DELETE'})
            const error = await failureMessage(response, "ส่งข้อมูลล้มเหลว");
            if (error) {
                await loadTasks();
                showError(error);
                return;
            }
            loadTasks();
        } );

        const editBtn = document.createElement("button");
        editBtn.type = "button";
        editBtn.textContent = "Edit";
        editBtn.addEventListener("click", function() {
            const editLabel = document.createElement("input");
            editLabel.type = "text";
            editLabel.value = task.detail;
            labelEl.replaceWith(editLabel);
            editLabel.focus();
            editLabel.addEventListener("keydown", function(event){
                editTaskDetail(event,task.id,editLabel)
            })
            editLabel.addEventListener("blur", function() {
                editLabel.replaceWith(labelEl);
            })
            editLabel.addEventListener("input", function() {
                editLabel.setCustomValidity("");
            })
        })        

        const labelEl = document.createElement("label");
        labelEl.htmlFor = `task-${task.id}`;
        labelEl.textContent = task.detail;

        itemEl.appendChild(checkboxEl);
        itemEl.appendChild(labelEl);
        itemEl.appendChild(editBtn);
        itemEl.appendChild(deleteBtn);
        taskListEl.appendChild(itemEl);
    }
    updateTaskCount(tasks);
}

async function editTaskDetail(event,id,editLabel) {
    if (event.key === "Enter") {
        const detail = editLabel.value;
        const response = await fetch(`/api/tasks/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({detail: detail})
        });
        const error = await failureMessage(response, "ส่งข้อมูลล้มเหลว");
        if (error) {
            editLabel.setCustomValidity(error);
            editLabel.reportValidity();
            return;
        }
        loadTasks();
    }
    if (event.key === "Escape") {
        loadTasks();
    }
}

async function loadTasks() {
    const response = await fetch('/api/tasks');
    const error = await failureMessage(response, "โหลดข้อมูลล้มเหลว");
    if (error) {
        showError(error);
        return;
    }
    hideError();
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

    const error = await failureMessage(response, "ส่งข้อมูลล้มเหลว");
    if (error) {
        newTaskInput.setCustomValidity(error);
        newTaskInput.reportValidity();
        return;
    }
    newTaskInput.value = "";
    loadTasks();
}

function updateTaskCount(tasks) {
    let taskCount = tasks.filter(t => t.done === false).length;
    document.getElementById("task-count").textContent = "เหลืออีก " + taskCount + " งาน";
}

function showError(message) {
    const errorEl = document.getElementById("task-error");
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function hideError() {
    const errorEl = document.getElementById("task-error");
    errorEl.hidden = true;
}

async function failureMessage(response, fallback) {
    if (response.status === 401) {
        window.location.href = '/';
        return "Unauthorized";
    }
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        return body.error || fallback;
    }
    return null;
}

loadTasks();
addTaskForm.addEventListener("submit", handleAddTask);
newTaskInput.addEventListener("input", function() {
    newTaskInput.setCustomValidity("");
    hideError();
});
