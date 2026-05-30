"use client";

import { useState, useEffect } from "react";
import { useIRIS } from "@/lib/store";
import { tasksApi, type Task } from "@/lib/api";

const PRIORITY_BADGE: Record<string, string> = {
  high:   "badge-high",
  urgent: "badge-high",
  medium: "badge-medium",
  low:    "badge-low",
};

function TaskItem({
  task,
  onToggle,
  onDelete,
}: {
  task: Task;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const isDone = task.status === "done";
  return (
    <div
      className={`glass rounded p-3 flex gap-3 items-start transition-opacity ${isDone ? "opacity-40" : ""} animate-fadeInUp`}
    >
      {/* Checkbox */}
      <button
        id={`iris-task-toggle-${task.id}`}
        onClick={onToggle}
        className={`mt-0.5 w-4 h-4 rounded-sm border flex items-center justify-center shrink-0 transition-all ${
          isDone
            ? "bg-[rgba(57,255,154,0.2)] border-[rgba(57,255,154,0.5)]"
            : "border-[rgba(74,224,255,0.3)] hover:border-[rgba(74,224,255,0.8)]"
        }`}
      >
        {isDone && <span className="text-[#39ff9a] text-[0.6rem]">✓</span>}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={`text-[0.75rem] leading-tight ${isDone ? "line-through" : ""}`}>
          {task.title}
        </p>
        {task.due_date && (
          <p className="text-[0.6rem] text-[rgba(74,224,255,0.35)] mt-0.5">
            Due {new Date(task.due_date).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* Priority + delete */}
      <div className="flex items-center gap-1.5 shrink-0">
        <span className={`badge ${PRIORITY_BADGE[task.priority] || "badge-low"}`}>
          {task.priority}
        </span>
        <button
          id={`iris-task-delete-${task.id}`}
          onClick={onDelete}
          className="text-[0.6rem] text-[rgba(255,74,110,0.4)] hover:text-[rgba(255,74,110,0.8)] transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

export default function TasksPanel() {
  const { state, dispatch } = useIRIS();
  const { tasks } = state;
  const [newTask, setNewTask] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [filter, setFilter] = useState<"all" | "pending" | "done">("pending");

  useEffect(() => {
    tasksApi.list().then((data) => {
      dispatch({ type: "SET_TASKS", payload: data });
    }).catch(() => {});
  }, [dispatch]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTask.trim()) return;
    try {
      const task = await tasksApi.create({ title: newTask, priority });
      dispatch({ type: "ADD_TASK", payload: task });
      setNewTask("");
    } catch {/* ignore */}
  }

  async function handleToggle(task: Task) {
    const newStatus = task.status === "done" ? "pending" : "done";
    try {
      const updated = await tasksApi.update(task.id, { status: newStatus });
      dispatch({ type: "UPDATE_TASK", payload: updated });
    } catch {/* ignore */}
  }

  async function handleDelete(taskId: number) {
    try {
      await tasksApi.delete(taskId);
      dispatch({ type: "REMOVE_TASK", payload: taskId });
    } catch {/* ignore */}
  }

  const filteredTasks = tasks.filter((t) => {
    if (filter === "pending") return t.status !== "done";
    if (filter === "done") return t.status === "done";
    return true;
  });

  const pendingCount = tasks.filter((t) => t.status !== "done").length;

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="section-header flex-1">Tasks</div>
        {pendingCount > 0 && (
          <span className="ml-2 badge badge-medium">{pendingCount} pending</span>
        )}
      </div>

      {/* New Task Form */}
      <form onSubmit={handleCreate} className="flex gap-2 shrink-0">
        <input
          id="iris-task-input"
          className="input-iris flex-1 text-[0.75rem] py-1.5"
          placeholder="Add a task..."
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
        />
        <select
          id="iris-task-priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as typeof priority)}
          className="input-iris w-20 text-[0.65rem] py-1.5 shrink-0"
        >
          <option value="low">Low</option>
          <option value="medium">Med</option>
          <option value="high">High</option>
        </select>
        <button
          type="submit"
          id="iris-task-add"
          className="btn-iris btn-iris-primary px-3 py-1.5 shrink-0"
          disabled={!newTask.trim()}
        >
          +
        </button>
      </form>

      {/* Filter tabs */}
      <div className="flex gap-2 shrink-0 border-b border-[rgba(74,224,255,0.1)] pb-2">
        {(["pending", "all", "done"] as const).map((f) => (
          <button
            key={f}
            id={`iris-task-filter-${f}`}
            onClick={() => setFilter(f)}
            className={`text-[0.6rem] uppercase tracking-wider px-2 py-1 rounded transition-colors ${
              filter === f
                ? "text-[#4ae0ff] bg-[rgba(74,224,255,0.08)]"
                : "text-[rgba(74,224,255,0.35)] hover:text-[rgba(74,224,255,0.6)]"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {filteredTasks.length === 0 && (
          <div className="text-center py-6 opacity-40">
            <p className="text-xl mb-1">✓</p>
            <p className="text-[0.65rem] uppercase tracking-wider">All clear</p>
          </div>
        )}
        {filteredTasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            onToggle={() => handleToggle(task)}
            onDelete={() => handleDelete(task.id)}
          />
        ))}
      </div>
    </div>
  );
}
