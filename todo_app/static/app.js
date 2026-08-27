const task1 = {
    id: 1,
    text: "Task1",
    done: false,
};

const task2 = {
    id: 2,
    text: "Task2",
    done: false,
};

const tasks = [task1, task2];
let nextTaskId = task2.id;

const taskListEl = document.getElementById("task-list");
const addTaskForm = document.querySelector(".add-task-form");
const newTaskInput = document.getElementById("new-task");

function renderTasks() {
    taskListEl.innerHTML = "";
    for (const task of tasks) {
        const itemEl = document.createElement("li");

        const checkboxEl = document.createElement("input");
        checkboxEl.type = "checkbox";
        checkboxEl.name = `task-${task.id}`;
        checkboxEl.id = `task-${task.id}`;

        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.textContent = "Delete";
        deleteBtn.className = "delete-btn";
        deleteBtn.addEventListener("click" , function(){
            tasks.splice(tasks.indexOf(task),1);
            renderTasks();
        } );


        const labelEl = document.createElement("label");
        labelEl.htmlFor = `task-${task.id}`;
        labelEl.textContent = task.text;

        itemEl.appendChild(checkboxEl);
        itemEl.appendChild(labelEl);
        itemEl.appendChild(deleteBtn);
        taskListEl.appendChild(itemEl);
    }
}

function handleAddTask(event) {
    event.preventDefault();

    const text = newTaskInput.value.trim();
    if (text === "") {
        newTaskInput.value = "";
        return;
    }

    nextTaskId++;
    const newTask = {
        id: nextTaskId,
        text: text,
        done: false,
    };

    tasks.push(newTask);
    newTaskInput.value = "";
    renderTasks();
}

renderTasks();
addTaskForm.addEventListener("submit", handleAddTask);
