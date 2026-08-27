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
    const taskCount = tasks.length;
    taskListEl.innerHTML = "";
    for (let i = 0; i < taskCount; i++) {
        const itemEl = document.createElement("li");

        const checkboxEl = document.createElement("input");
        checkboxEl.type = "checkbox";
        checkboxEl.name = `task-${tasks[i].id}`;
        checkboxEl.id = `task-${tasks[i].id}`;

        const labelEl = document.createElement("label");
        labelEl.htmlFor = `task-${tasks[i].id}`;
        labelEl.textContent = tasks[i].text;

        itemEl.appendChild(checkboxEl);
        itemEl.appendChild(labelEl);
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
