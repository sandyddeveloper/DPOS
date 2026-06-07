"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  LayoutDashboard,
  Briefcase,
  Clipboard,
  Activity,
  Plus,
  Trash2,
  Search,
  Copy,
  CheckCircle,
  Circle,
  Cpu,
  Layers,
  Clock,
  RotateCw,
  X,
  ExternalLink,
  ChevronRight,
  Shield,
  FileCode,
  Terminal,
  Database,
  Link as LinkIcon
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [backendConnected, setBackendConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Data States
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [clips, setClips] = useState([]);
  const [monitorSnap, setMonitorSnap] = useState({
    cpu_percent: 0,
    ram_percent: 0,
    ram_used_gb: 0,
    ram_total_gb: 0,
    ports: [],
    containers: [],
    docker_online: false
  });
  
  // History States for graphs
  const [cpuHistory, setCpuHistory] = useState([]);
  const [ramHistory, setRamHistory] = useState([]);
  
  // Search and Filter States
  const [projectSearch, setProjectSearch] = useState("");
  const [clipSearch, setClipSearch] = useState("");
  const [clipFilter, setClipFilter] = useState("ALL");
  
  // Toast Notification
  const [toast, setToast] = useState(null);
  
  // Modal States
  const [showAddProjectModal, setShowAddProjectModal] = useState(false);
  const [newProject, setNewProject] = useState({
    name: "",
    path: "",
    tags: "",
    serviceType: "port",
    servicePort: "",
    serviceProcess: ""
  });
  
  // Task Inline Form State
  const [showAddTaskProject, setShowAddTaskProject] = useState(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDueDate, setNewTaskDueDate] = useState(new Date().toISOString().split('T')[0]);

  // Toast Helper
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // 1. API Polling and Backend Status check
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/monitor/snapshot");
        if (res.ok) {
          if (!backendConnected) {
            setBackendConnected(true);
            setLoading(false);
            showToast("Connected to DPOS Backend Sidecar", "success");
            // Initial fetches
            fetchProjects();
            fetchTasks();
            fetchClipboard();
          }
        }
      } catch (err) {
        setBackendConnected(false);
        setLoading(true);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 3000);
    return () => clearInterval(interval);
  }, [backendConnected]);

  // 2. Real-time metric updater (every 2 seconds when tab is monitor or dashboard)
  useEffect(() => {
    if (!backendConnected) return;
    
    const updateMetrics = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/monitor/snapshot");
        if (res.ok) {
          const data = await res.json();
          setMonitorSnap(data);
          
          // Add to history (max 20 points)
          setCpuHistory(prev => [...prev.slice(-19), data.cpu_percent]);
          setRamHistory(prev => [...prev.slice(-19), data.ram_percent]);
        }
      } catch (err) {
        console.error("Metrics capture failed:", err);
      }
    };

    updateMetrics();
    const interval = setInterval(updateMetrics, 2000);
    return () => clearInterval(interval);
  }, [backendConnected, activeTab]);

  // Data Fetching Functions
  const fetchProjects = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects");
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/tasks");
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchClipboard = async (query = "", filter = "ALL") => {
    try {
      const url = new URL("http://127.0.0.1:8000/api/clipboard");
      if (query) url.searchParams.append("query", query);
      if (filter && filter !== "ALL") url.searchParams.append("filter", filter);
      
      const res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json();
        setClips(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Clipboard filters and query watch
  useEffect(() => {
    if (!backendConnected) return;
    const delayDebounce = setTimeout(() => {
      fetchClipboard(clipSearch, clipFilter);
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [clipSearch, clipFilter, backendConnected]);

  // Actions
  const handleTriggerScan = async () => {
    showToast("Starting manual filesystem project scan...", "info");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/scan", { method: "POST" });
      if (res.ok) {
        showToast("Scan complete!", "success");
        fetchProjects();
      } else {
        showToast("Scan failed", "error");
      }
    } catch (e) {
      showToast("Network error during scan", "error");
    }
  };

  const handleAddProject = async (e) => {
    e.preventDefault();
    if (!newProject.name || !newProject.path) {
      showToast("Name and Path are required", "error");
      return;
    }

    const services = [];
    if (newProject.serviceType === "port" && newProject.servicePort) {
      services.push({ type: "port", port: parseInt(newProject.servicePort) });
    } else if (newProject.serviceType === "process" && newProject.serviceProcess) {
      services.push({ type: "process", process_name: newProject.serviceProcess });
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newProject.name,
          path: newProject.path,
          tags: newProject.tags,
          services: services
        })
      });
      if (res.ok) {
        showToast("Project added successfully!");
        setShowAddProjectModal(false);
        setNewProject({
          name: "",
          path: "",
          tags: "",
          serviceType: "port",
          servicePort: "",
          serviceProcess: ""
        });
        fetchProjects();
      } else {
        showToast("Failed to add project", "error");
      }
    } catch (err) {
      showToast("Network error adding project", "error");
    }
  };

  const handleDeleteProject = async (id) => {
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/projects/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Project deleted");
        fetchProjects();
      } else {
        showToast("Failed to delete project", "error");
      }
    } catch (e) {
      showToast("Network error", "error");
    }
  };

  const handleToggleTask = async (task) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tasks/${task.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: !task.completed })
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddTask = async (projectId) => {
    if (!newTaskTitle.trim()) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTaskTitle,
          due_date: newTaskDueDate,
          project_id: projectId
        })
      });
      if (res.ok) {
        showToast("Task added!");
        setNewTaskTitle("");
        setShowAddTaskProject(null);
        fetchTasks();
      }
    } catch (err) {
      showToast("Error adding task", "error");
    }
  };

  const handleDeleteTask = async (id) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tasks/${id}`, { method: "DELETE" });
      if (res.ok) {
        fetchTasks();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCopyClip = async (text) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/clipboard/copy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        showToast("Copied content back to OS clipboard!");
      }
    } catch (err) {
      showToast("Failed to copy", "error");
    }
  };

  const handleDeleteClip = async (id) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/clipboard/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Clipboard entry deleted");
        fetchClipboard(clipSearch, clipFilter);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Sparkline Generator Helper
  const getSparklinePoints = (history) => {
    if (history.length < 2) return "";
    const max = 100;
    const min = 0;
    const width = 120;
    const height = 30;
    const padding = 2;
    
    return history.map((val, idx) => {
      const x = (idx / (history.length - 1)) * (width - 2 * padding) + padding;
      const y = height - ((val - min) / (max - min)) * (height - 2 * padding) - padding;
      return `${x},${y}`;
    }).join(" ");
  };

  // Filter project listing
  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
    p.tags.some(t => t.toLowerCase().includes(projectSearch.toLowerCase()))
  );

  // Task summary percentages
  const completedTasksCount = tasks.filter(t => t.completed).length;
  const totalTasksCount = tasks.length;
  const taskCompletionPercentage = totalTasksCount > 0 ? Math.round((completedTasksCount / totalTasksCount) * 100) : 0;

  // Render Loader if offline
  if (loading || !backendConnected) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#050508] text-white">
        <div className="relative flex flex-col items-center p-8 rounded-2xl glass-panel-glow max-w-sm text-center">
          <div className="absolute inset-0 bg-radial glow-bg-purple opacity-20 pointer-events-none rounded-2xl"></div>
          
          <div className="relative w-16 h-16 mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-purple-500 border-t-transparent animate-spin"></div>
          </div>
          
          <h2 className="text-xl font-bold tracking-wider text-purple-400 text-glow-purple mb-2">DPOS BOOTING</h2>
          <p className="text-sm text-zinc-400">Connecting to the DPOS Python local sidecar on port 8000...</p>
          <div className="mt-6 flex items-center text-xs text-zinc-500 gap-2 bg-black/40 px-3 py-1.5 rounded-full border border-white/5">
            <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
            Waiting for sidecar process initialization
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#050508] text-zinc-100 selection:bg-purple-500/30 selection:text-purple-300">
      
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg border shadow-xl transition-all duration-300 animate-slide-in ${
          toast.type === "error" 
            ? "bg-red-950/80 border-red-800 text-red-200" 
            : toast.type === "info" 
            ? "bg-cyan-950/80 border-cyan-800 text-cyan-200" 
            : "bg-purple-950/80 border-purple-800 text-purple-200"
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            toast.type === "error" ? "bg-red-400" : toast.type === "info" ? "bg-cyan-400" : "bg-purple-400 animate-ping"
          }`} />
          <span className="text-sm font-medium">{toast.message}</span>
        </div>
      )}

      {/* SIDEBAR NAVIGATION */}
      <aside className="w-64 border-r border-white/5 bg-[#09090F]/90 backdrop-blur-xl flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center px-6 gap-3 border-b border-white/5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-500 flex items-center justify-center font-bold text-black text-sm tracking-wider shadow-lg shadow-purple-600/20">
              DP
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
                DPOS WORKSTATION
              </h1>
              <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider block -mt-0.5">
                v0.1.0 (Web Native)
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "dashboard"
                  ? "bg-purple-500/10 border-l-2 border-purple-500 text-purple-400 bg-gradient-to-r from-purple-950/20 to-transparent"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }`}
            >
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab("projects")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "projects"
                  ? "bg-purple-500/10 border-l-2 border-purple-500 text-purple-400 bg-gradient-to-r from-purple-950/20 to-transparent"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }`}
            >
              <Briefcase size={18} />
              <span>Projects ({projects.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("clipboard")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "clipboard"
                  ? "bg-purple-500/10 border-l-2 border-purple-500 text-purple-400 bg-gradient-to-r from-purple-950/20 to-transparent"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }`}
            >
              <Clipboard size={18} />
              <span>Clipboard ({clips.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("monitor")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === "monitor"
                  ? "bg-purple-500/10 border-l-2 border-purple-500 text-purple-400 bg-gradient-to-r from-purple-950/20 to-transparent"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }`}
            >
              <Activity size={18} />
              <span>System Monitor</span>
            </button>
          </nav>
        </div>

        {/* Quick status bar at the bottom */}
        <div className="p-4 border-t border-white/5 bg-black/20 text-xs text-zinc-500 space-y-2">
          <div className="flex items-center justify-between">
            <span>Daemon Sidecar</span>
            <span className="flex items-center gap-1 text-emerald-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              ONLINE
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Active Services</span>
            <span className="font-semibold text-zinc-300">
              {projects.filter(p => p.is_active).length}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Sys missed scan</span>
            <span className="text-zinc-300">Auto Recovered</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <main className="flex-1 flex flex-col overflow-y-auto min-h-screen">
        
        {/* TOP STATUS BAR */}
        <header className="h-16 border-b border-white/5 bg-[#050508]/50 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <span className="text-sm font-bold tracking-widest text-zinc-400 uppercase">
              {activeTab}
            </span>
            <div className="h-4 w-px bg-white/10"></div>
            <button 
              onClick={handleTriggerScan}
              className="flex items-center gap-1.5 px-3 py-1 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 rounded-full text-xs font-semibold text-purple-400 transition"
            >
              <RotateCw size={12} className="animate-spin-slow" />
              Scan Folders
            </button>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex gap-4 items-center">
              <div className="text-right">
                <span className="text-[10px] text-zinc-500 font-bold block leading-none">CPU</span>
                <span className="text-xs text-zinc-300 font-bold">{monitorSnap.cpu_percent}%</span>
              </div>
              <div className="w-20 bg-zinc-950 h-1.5 rounded-full overflow-hidden border border-white/5">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-purple-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${monitorSnap.cpu_percent}%` }}
                ></div>
              </div>
            </div>
            
            <div className="flex gap-4 items-center">
              <div className="text-right">
                <span className="text-[10px] text-zinc-500 font-bold block leading-none">RAM</span>
                <span className="text-xs text-zinc-300 font-bold">{Math.round(monitorSnap.ram_percent)}%</span>
              </div>
              <div className="w-20 bg-zinc-950 h-1.5 rounded-full overflow-hidden border border-white/5">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${monitorSnap.ram_percent}%` }}
                ></div>
              </div>
            </div>
          </div>
        </header>

        {/* PANEL CONTENT WITH TABS */}
        <div className="p-8 flex-1 max-w-7xl w-full mx-auto space-y-8">
          
          {/* TAB 1: DASHBOARD */}
          {activeTab === "dashboard" && (
            <div className="space-y-8 animate-fade-in">
              {/* Header glass panel banner */}
              <div className="relative rounded-2xl glass-panel-glow p-8 overflow-hidden border border-purple-500/15">
                <div className="absolute inset-0 bg-radial glow-bg-purple opacity-20 pointer-events-none"></div>
                <div className="relative z-10 max-w-xl">
                  <span className="text-xs text-purple-400 font-bold tracking-widest uppercase mb-1 block">
                    Welcome back to DPOS
                  </span>
                  <h2 className="text-3xl font-extrabold tracking-tight text-white mb-2">
                    Animated Station Manager
                  </h2>
                  <p className="text-zinc-400 text-sm leading-relaxed">
                    Automated background process checks, clipboard pattern history trackers, 
                    and local Git repo indicators are active. Use the side tabs to browse.
                  </p>
                </div>
              </div>

              {/* Grid Layout: Circular progress bar & statistics cards */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Circular Progress Gauge Panel */}
                <div className="lg:col-span-1 rounded-2xl glass-panel p-6 flex flex-col items-center justify-center text-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-radial glow-bg-purple opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity"></div>
                  
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">
                    Workstation Task Progress
                  </h3>
                  
                  {/* Gauge SVG ring */}
                  <div className="relative w-44 h-44 flex items-center justify-center">
                    <svg className="w-full h-full transform -rotate-90">
                      {/* Inner Ring shadow */}
                      <circle
                        cx="88"
                        cy="88"
                        r="74"
                        className="stroke-[#101017] fill-transparent"
                        strokeWidth="10"
                      />
                      {/* Glowing indicator path */}
                      <circle
                        cx="88"
                        cy="88"
                        r="74"
                        className="stroke-purple-500 fill-transparent transition-all duration-1000 ease-out"
                        strokeWidth="8"
                        strokeDasharray={2 * Math.PI * 74}
                        strokeDashoffset={2 * Math.PI * 74 * (1 - taskCompletionPercentage / 100)}
                        strokeLinecap="round"
                      />
                    </svg>
                    
                    {/* Centered Stats Text */}
                    <div className="absolute flex flex-col items-center">
                      <span className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-br from-white via-purple-300 to-purple-600 text-glow-purple">
                        {taskCompletionPercentage}%
                      </span>
                      <span className="text-[10px] text-zinc-500 font-bold uppercase mt-1">
                        {completedTasksCount} / {totalTasksCount} Tasks
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-6 text-xs text-zinc-500 max-w-[200px] leading-relaxed">
                    Aggregate status of active tasks associated with registered project directories.
                  </div>
                </div>

                {/* Grid of Glowing Cards */}
                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
                  
                  {/* Stat Card 1: Active Projects */}
                  <div className="rounded-2xl glass-panel p-6 relative overflow-hidden group hover:border-cyan-500/30 transition-all duration-300">
                    <div className="absolute inset-0 bg-radial glow-bg-cyan opacity-5 group-hover:opacity-10 pointer-events-none transition-opacity"></div>
                    <div className="flex justify-between items-start mb-4">
                      <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
                        <Briefcase size={20} />
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">
                          Total Projects
                        </span>
                        <span className="text-4xl font-bold tracking-tight text-white">
                          {projects.length}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-semibold mb-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                        {projects.filter(p => p.is_active).length} active running sidecars
                      </div>
                      <p className="text-zinc-500 text-[11px] leading-relaxed">
                        Registered projects folder scan checks automatically for running ports/processes.
                      </p>
                    </div>
                  </div>

                  {/* Stat Card 2: Clipboard Records */}
                  <div className="rounded-2xl glass-panel p-6 relative overflow-hidden group hover:border-purple-500/30 transition-all duration-300">
                    <div className="absolute inset-0 bg-radial glow-bg-purple opacity-5 group-hover:opacity-10 pointer-events-none transition-opacity"></div>
                    <div className="flex justify-between items-start mb-4">
                      <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400">
                        <Clipboard size={20} />
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">
                          Clipboard History
                        </span>
                        <span className="text-4xl font-bold tracking-tight text-white">
                          {clips.length}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-purple-400 font-semibold mb-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"></span>
                        Watcher active (1s polling)
                      </div>
                      <p className="text-zinc-500 text-[11px] leading-relaxed">
                        Fuzzy indexing is built directly with Whoosh for instant exact search.
                      </p>
                    </div>
                  </div>

                  {/* Stat Card 3: Scheduler check */}
                  <div className="rounded-2xl glass-panel p-6 relative overflow-hidden group hover:border-emerald-500/30 transition-all duration-300">
                    <div className="absolute inset-0 bg-radial glow-bg-purple opacity-5 group-hover:opacity-10 pointer-events-none transition-opacity"></div>
                    <div className="flex justify-between items-start mb-4">
                      <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
                        <Clock size={20} />
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">
                          Daily 1AM Scan
                        </span>
                        <span className="text-lg font-bold tracking-wider text-emerald-400 uppercase">
                          REGISTERED
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold mb-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        Task Scheduler Active
                      </div>
                      <p className="text-zinc-500 text-[11px] leading-relaxed">
                        Registers via standard user flags without requiring administrator access.
                      </p>
                    </div>
                  </div>

                  {/* Stat Card 4: Docker Monitor */}
                  <div className="rounded-2xl glass-panel p-6 relative overflow-hidden group hover:border-yellow-500/30 transition-all duration-300">
                    <div className="absolute inset-0 bg-radial glow-bg-cyan opacity-5 group-hover:opacity-10 pointer-events-none transition-opacity"></div>
                    <div className="flex justify-between items-start mb-4">
                      <div className="p-3 rounded-xl bg-yellow-500/10 text-yellow-400">
                        <Layers size={20} />
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">
                          Docker Status
                        </span>
                        <span className={`text-lg font-bold tracking-wider uppercase ${
                          monitorSnap.docker_online ? "text-emerald-400" : "text-zinc-500"
                        }`}>
                          {monitorSnap.docker_online ? "ONLINE" : "OFFLINE"}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-zinc-400 mb-1">
                        <span>Containers:</span>
                        <span className="font-bold text-zinc-200">
                          {monitorSnap.containers.length} total
                        </span>
                      </div>
                      <p className="text-zinc-500 text-[11px] leading-relaxed">
                        Reads directly from local environment Docker Daemon using native docker SDK.
                      </p>
                    </div>
                  </div>

                </div>

              </div>

              {/* Row: Active Tasks Quick Widget */}
              <div className="rounded-2xl glass-panel p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-base font-bold text-white">Active Tasks</h3>
                    <p className="text-xs text-zinc-400">Tasks associated with your registered workspace directories</p>
                  </div>
                  <button
                    onClick={() => setActiveTab("projects")}
                    className="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1"
                  >
                    Manage Projects <ChevronRight size={14} />
                  </button>
                </div>

                <div className="space-y-3">
                  {tasks.length === 0 ? (
                    <div className="text-center py-6 text-zinc-500 text-sm border border-dashed border-white/5 rounded-xl">
                      No active tasks found. Go to Projects and select a project to seed tasks!
                    </div>
                  ) : (
                    tasks.map(task => {
                      const project = projects.find(p => p.id === task.project_id);
                      return (
                        <div 
                          key={task.id} 
                          className="flex items-center justify-between p-4 rounded-xl border border-white/5 bg-[#09090F]/40 hover:bg-[#0E0E17]/60 transition group"
                        >
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => handleToggleTask(task)}
                              className={`text-zinc-500 hover:text-purple-400 transition ${
                                task.completed ? "text-purple-400" : ""
                              }`}
                            >
                              {task.completed ? <CheckCircle size={18} /> : <Circle size={18} />}
                            </button>
                            <div>
                              <span className={`text-sm ${
                                task.completed ? "line-through text-zinc-500" : "text-zinc-200"
                              }`}>
                                {task.title}
                              </span>
                              <div className="flex items-center gap-2 mt-0.5">
                                {project && (
                                  <span className="text-[10px] bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full border border-purple-500/15">
                                    {project.name}
                                  </span>
                                )}
                                <span className="text-[10px] text-zinc-500 font-semibold flex items-center gap-1">
                                  Due: {task.due_date}
                                </span>
                              </div>
                            </div>
                          </div>

                          <button
                            onClick={() => handleDeleteTask(task.id)}
                            className="text-zinc-500 hover:text-red-400 p-2 rounded-lg hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: PROJECTS */}
          {activeTab === "projects" && (
            <div className="space-y-8 animate-fade-in">
              
              {/* Header and Controls Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#09090F]/40 p-4 rounded-2xl border border-white/5 backdrop-blur-md">
                <div className="relative max-w-sm w-full">
                  <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400" />
                  <input
                    type="text"
                    placeholder="Search projects by name or tag..."
                    value={projectSearch}
                    onChange={(e) => setProjectSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                  />
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <button
                    onClick={() => setShowAddProjectModal(true)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-purple-600/10 hover:shadow-purple-600/25 transition"
                  >
                    <Plus size={16} />
                    Add Project
                  </button>
                </div>
              </div>

              {/* Grid of Projects */}
              {filteredProjects.length === 0 ? (
                <div className="text-center py-20 rounded-2xl border border-dashed border-white/10 glass-panel">
                  <span className="text-sm text-zinc-500 block mb-2">No projects found.</span>
                  <button 
                    onClick={() => setShowAddProjectModal(true)}
                    className="text-xs text-purple-400 font-semibold hover:underline"
                  >
                    Create a new DPOS project card entry now
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {filteredProjects.map(project => {
                    const projectTasks = tasks.filter(t => t.project_id === project.id);
                    const completedProjTasks = projectTasks.filter(t => t.completed).length;
                    const completionRate = projectTasks.length > 0 ? Math.round((completedProjTasks / projectTasks.length) * 100) : 0;
                    
                    return (
                      <div 
                        key={project.id} 
                        className={`rounded-2xl glass-panel p-6 border transition-all duration-300 relative ${
                          project.is_active ? "border-cyan-500/20" : "border-white/5"
                        }`}
                      >
                        {/* Top Info section */}
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-lg font-bold text-white tracking-tight">{project.name}</h4>
                              <span className={`w-2 h-2 rounded-full ${
                                project.is_active 
                                  ? "bg-cyan-400 animate-pulse shadow-sm shadow-cyan-400" 
                                  : "bg-zinc-700"
                              }`} />
                            </div>
                            <span className="text-[10px] text-zinc-500 font-mono block mt-1 select-all hover:text-zinc-400">
                              {project.path}
                            </span>
                          </div>

                          <button
                            onClick={() => handleDeleteProject(project.id)}
                            className="text-zinc-500 hover:text-red-400 p-2 rounded-lg hover:bg-red-500/10 transition"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>

                        {/* Project tags row */}
                        <div className="flex flex-wrap gap-1.5 mb-6">
                          {project.tags.length > 0 ? (
                            project.tags.map((tag, idx) => (
                              <span 
                                key={idx} 
                                className="text-[10px] bg-white/5 text-zinc-400 px-2 py-0.5 rounded-full border border-white/5"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-zinc-600 italic">No tags</span>
                          )}
                        </div>

                        {/* Service checker & git updates */}
                        <div className="grid grid-cols-2 gap-4 p-3 rounded-xl bg-black/40 border border-white/5 mb-6 text-xs">
                          <div>
                            <span className="text-zinc-500 block text-[9px] font-bold uppercase tracking-wider mb-1">
                              Sidecar Services
                            </span>
                            <div className="space-y-1">
                              {project.services.map((svc, sIdx) => (
                                <div key={sIdx} className="flex items-center gap-1.5 text-zinc-300">
                                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                  <span>
                                    {svc.type === "port" ? `Port: ${svc.port}` : `Proc: ${svc.process_name}`}
                                  </span>
                                </div>
                              ))}
                              {project.services.length === 0 && (
                                <span className="text-zinc-600 italic">None</span>
                              )}
                            </div>
                          </div>

                          <div>
                            <span className="text-zinc-500 block text-[9px] font-bold uppercase tracking-wider mb-1">
                              Git Monitor
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`w-1.5 h-1.5 rounded-full ${project.git_changes > 0 ? "bg-yellow-400" : "bg-emerald-400"}`} />
                              <span className="text-zinc-300">
                                {project.git_changes > 0 ? `${project.git_changes} uncommitted files` : "Clean workspace"}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Project progress and tasks list */}
                        <div className="space-y-4">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-zinc-400 font-semibold">Tasks Completed</span>
                            <span className="text-purple-400 font-bold">{completionRate}%</span>
                          </div>
                          
                          <div className="w-full bg-zinc-950 h-1.5 rounded-full overflow-hidden border border-white/5">
                            <div 
                              className="bg-purple-500 h-full rounded-full transition-all duration-700" 
                              style={{ width: `${completionRate}%` }}
                            ></div>
                          </div>

                          {/* Quick tasks viewer */}
                          <div className="space-y-2">
                            {projectTasks.map(task => (
                              <div key={task.id} className="flex items-center justify-between text-xs p-2 bg-[#09090F]/20 rounded-lg hover:bg-black/30 border border-white/5 group/task">
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => handleToggleTask(task)}
                                    className={`text-zinc-500 hover:text-purple-400 transition ${
                                      task.completed ? "text-purple-400" : ""
                                    }`}
                                  >
                                    {task.completed ? <CheckCircle size={14} /> : <Circle size={14} />}
                                  </button>
                                  <span className={task.completed ? "line-through text-zinc-500" : "text-zinc-300"}>
                                    {task.title}
                                  </span>
                                </div>
                                <button
                                  onClick={() => handleDeleteTask(task.id)}
                                  className="text-zinc-600 hover:text-red-400 transition opacity-0 group-hover/task:opacity-100"
                                >
                                  <X size={12} />
                                </button>
                              </div>
                            ))}
                          </div>

                          {/* Add task block */}
                          {showAddTaskProject === project.id ? (
                            <div className="p-3 bg-black/40 border border-purple-500/10 rounded-xl space-y-2.5">
                              <input
                                type="text"
                                placeholder="Task description..."
                                value={newTaskTitle}
                                onChange={(e) => setNewTaskTitle(e.target.value)}
                                className="w-full px-3 py-1.5 bg-black/60 border border-white/5 rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-purple-500/40"
                              />
                              <div className="flex gap-2">
                                <input
                                  type="date"
                                  value={newTaskDueDate}
                                  onChange={(e) => setNewTaskDueDate(e.target.value)}
                                  className="flex-1 px-3 py-1 bg-black/60 border border-white/5 rounded-lg text-xs text-zinc-400 focus:outline-none"
                                />
                                <button
                                  onClick={() => handleAddTask(project.id)}
                                  className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => setShowAddTaskProject(null)}
                                  className="px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 rounded-lg text-xs"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => {
                                setShowAddTaskProject(project.id);
                                setNewTaskTitle("");
                              }}
                              className="w-full flex items-center justify-center gap-1.5 py-2 border border-dashed border-white/5 hover:border-purple-500/20 text-xs text-zinc-500 hover:text-purple-400 rounded-xl transition"
                            >
                              <Plus size={14} />
                              Add Task Card
                            </button>
                          )}
                        </div>

                      </div>
                    );
                  })}
                </div>
              )}

            </div>
          )}

          {/* TAB 3: CLIPBOARD */}
          {activeTab === "clipboard" && (
            <div className="space-y-8 animate-fade-in">
              
              {/* Filter controls row */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#09090F]/40 p-4 rounded-2xl border border-white/5 backdrop-blur-md">
                <div className="relative max-w-sm w-full">
                  <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400" />
                  <input
                    type="text"
                    placeholder="Search clipboard index history..."
                    value={clipSearch}
                    onChange={(e) => setClipSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                  />
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {["ALL", "TEXT", "URL", "SQL", "TOKEN", "CODE"].map(filterVal => (
                    <button
                      key={filterVal}
                      onClick={() => setClipFilter(filterVal)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                        clipFilter === filterVal
                          ? "bg-purple-600 text-white shadow-md shadow-purple-600/10"
                          : "bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-zinc-200"
                      }`}
                    >
                      {filterVal}
                    </button>
                  ))}
                </div>
              </div>

              {/* Clips List */}
              <div className="space-y-4">
                {clips.length === 0 ? (
                  <div className="text-center py-20 rounded-2xl border border-dashed border-white/10 glass-panel">
                    <span className="text-sm text-zinc-500 block">No clipboard entries found.</span>
                    <span className="text-xs text-zinc-600 block mt-1">Copy some text to automatically record history items.</span>
                  </div>
                ) : (
                  clips.map(clip => {
                    const dateObj = new Date(clip.timestamp);
                    const formattedTime = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    const formattedDate = dateObj.toLocaleDateString();
                    
                    return (
                      <div 
                        key={clip.id} 
                        className="rounded-2xl glass-panel p-5 hover:border-purple-500/20 hover:shadow-lg hover:shadow-purple-500/5 transition duration-300 group relative"
                      >
                        {/* Header details */}
                        <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2 text-xs">
                          <div className="flex items-center gap-2">
                            <span className="text-zinc-500 font-bold uppercase flex items-center gap-1 select-none">
                              <Clock size={12} />
                              {formattedDate} {formattedTime}
                            </span>
                            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${
                              clip.category === "url" 
                                ? "bg-cyan-500/15 text-cyan-400 border border-cyan-500/20" 
                                : clip.category === "code" 
                                ? "bg-purple-500/15 text-purple-400 border border-purple-500/20" 
                                : clip.category === "sql"
                                ? "bg-yellow-500/15 text-yellow-400 border border-yellow-500/20"
                                : clip.category === "token"
                                ? "bg-red-500/15 text-red-400 border border-red-500/20"
                                : "bg-white/5 text-zinc-400 border border-white/5"
                            }`}>
                              {clip.category}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleCopyClip(clip.content)}
                              className="text-zinc-400 hover:text-purple-400 p-1.5 rounded-lg hover:bg-purple-500/10 transition"
                              title="Copy to clipboard"
                            >
                              <Copy size={13} />
                            </button>
                            <button
                              onClick={() => handleDeleteClip(clip.id)}
                              className="text-zinc-400 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition"
                              title="Delete entry"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>

                        {/* Content text codebox */}
                        <div className="relative">
                          <pre className="text-zinc-300 text-xs font-mono bg-black/40 p-4 rounded-xl border border-white/5 overflow-x-auto select-text whitespace-pre-wrap max-h-48 overflow-y-auto">
                            {clip.content}
                          </pre>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

            </div>
          )}

          {/* TAB 4: SYSTEM MONITOR */}
          {activeTab === "monitor" && (
            <div className="space-y-8 animate-fade-in">
              
              {/* Dynamic stats row (with charts) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* CPU Real-time Box */}
                <div className="rounded-2xl glass-panel p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
                        <Cpu size={18} />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">CPU Utilization</h3>
                        <p className="text-[10px] text-zinc-500">Updates live every 2 seconds</p>
                      </div>
                    </div>
                    <span className="text-2xl font-black text-purple-400 text-glow-purple">
                      {monitorSnap.cpu_percent}%
                    </span>
                  </div>

                  {/* Sparkline canvas */}
                  <div className="h-24 bg-black/40 border border-white/5 rounded-xl flex items-end p-2 relative overflow-hidden">
                    {cpuHistory.length > 1 ? (
                      <svg className="w-full h-full overflow-visible">
                        <defs>
                          <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        {/* Area path */}
                        <path
                          d={`M 2,96 ${cpuHistory.map((val, idx) => {
                            const x = (idx / (cpuHistory.length - 1)) * 320;
                            const y = 96 - (val / 100) * 80;
                            return `L ${x},${y}`;
                          }).join(" ")} L 320,96 Z`}
                          fill="url(#cpuGrad)"
                        />
                        {/* Stroke path */}
                        <polyline
                          fill="none"
                          stroke="#a855f7"
                          strokeWidth="2"
                          points={cpuHistory.map((val, idx) => {
                            const x = (idx / (cpuHistory.length - 1)) * 320;
                            const y = 96 - (val / 100) * 80;
                            return `${x},${y}`;
                          }).join(" ")}
                        />
                      </svg>
                    ) : (
                      <span className="text-xs text-zinc-600 m-auto">Gleaning metrics data...</span>
                    )}
                  </div>
                </div>

                {/* RAM Real-time Box */}
                <div className="rounded-2xl glass-panel p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
                        <Activity size={18} />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">RAM Utilization</h3>
                        <p className="text-[10px] text-zinc-500">
                          {monitorSnap.ram_used_gb.toFixed(2)} GB used of {monitorSnap.ram_total_gb.toFixed(1)} GB total
                        </p>
                      </div>
                    </div>
                    <span className="text-2xl font-black text-cyan-400 text-glow-cyan">
                      {Math.round(monitorSnap.ram_percent)}%
                    </span>
                  </div>

                  {/* Sparkline canvas */}
                  <div className="h-24 bg-black/40 border border-white/5 rounded-xl flex items-end p-2 relative overflow-hidden">
                    {ramHistory.length > 1 ? (
                      <svg className="w-full h-full overflow-visible">
                        <defs>
                          <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        {/* Area path */}
                        <path
                          d={`M 2,96 ${ramHistory.map((val, idx) => {
                            const x = (idx / (ramHistory.length - 1)) * 320;
                            const y = 96 - (val / 100) * 80;
                            return `L ${x},${y}`;
                          }).join(" ")} L 320,96 Z`}
                          fill="url(#ramGrad)"
                        />
                        {/* Stroke path */}
                        <polyline
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="2"
                          points={ramHistory.map((val, idx) => {
                            const x = (idx / (ramHistory.length - 1)) * 320;
                            const y = 96 - (val / 100) * 80;
                            return `${x},${y}`;
                          }).join(" ")}
                        />
                      </svg>
                    ) : (
                      <span className="text-xs text-zinc-600 m-auto">Gleaning metrics data...</span>
                    )}
                  </div>
                </div>

              </div>

              {/* Sub-grid: Ports and Docker List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Listening Ports Box */}
                <div className="rounded-2xl glass-panel p-6 space-y-4">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest block">
                    Active Listening Ports
                  </span>
                  
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {monitorSnap.ports.length === 0 ? (
                      <div className="text-center py-8 text-zinc-500 text-xs italic">
                        No active listening ports discovered.
                      </div>
                    ) : (
                      monitorSnap.ports.map((p, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-xl border border-white/5 bg-[#09090F]/40 hover:bg-[#0E0E17]/60 transition text-xs font-mono">
                          <span className="text-purple-400 font-bold">Port {p.port}</span>
                          <span className="text-zinc-500">PID {p.pid || "N/A"}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Docker containers state list */}
                <div className="rounded-2xl glass-panel p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest block">
                      Docker Container States
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      monitorSnap.docker_online ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    }`}>
                      {monitorSnap.docker_online ? "DAEMON OK" : "DAEMON OFF"}
                    </span>
                  </div>
                  
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {!monitorSnap.docker_online ? (
                      <div className="text-center py-8 text-zinc-500 text-xs italic">
                        Docker Desktop daemon is offline. Start Docker to watch container health.
                      </div>
                    ) : monitorSnap.containers.length === 0 ? (
                      <div className="text-center py-8 text-zinc-500 text-xs italic">
                        No docker containers running or stopped.
                      </div>
                    ) : (
                      monitorSnap.containers.map((c, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-xl border border-white/5 bg-[#09090F]/40 hover:bg-[#0E0E17]/60 transition text-xs">
                          <span className="text-zinc-200 font-semibold truncate max-w-[150px]">{c.name}</span>
                          <span className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] ${
                            c.status === "RUNNING"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-zinc-800 text-zinc-400"
                          }`}>
                            {c.status}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>

            </div>
          )}

        </div>
      </main>

      {/* ADD PROJECT MODAL DIALOG */}
      {showAddProjectModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="rounded-2xl glass-panel-glow max-w-md w-full p-6 border border-purple-500/25 relative overflow-hidden">
            <div className="absolute inset-0 bg-radial glow-bg-purple opacity-20 pointer-events-none rounded-2xl"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-white tracking-tight">Add Project Folder</h3>
                <button
                  onClick={() => setShowAddProjectModal(false)}
                  className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleAddProject} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-1.5">Project Name</label>
                  <input
                    type="text"
                    required
                    value={newProject.name}
                    onChange={(e) => setNewProject(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g. My Nextjs App"
                    className="w-full px-4 py-2.5 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-1.5">Absolute Directory Path</label>
                  <input
                    type="text"
                    required
                    value={newProject.path}
                    onChange={(e) => setNewProject(prev => ({ ...prev, path: e.target.value }))}
                    placeholder="C:/Users/name/Projects/my-app"
                    className="w-full px-4 py-2.5 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-1.5">Tags (Comma-separated)</label>
                  <input
                    type="text"
                    value={newProject.tags}
                    onChange={(e) => setNewProject(prev => ({ ...prev, tags: e.target.value }))}
                    placeholder="Nextjs, React, Node"
                    className="w-full px-4 py-2.5 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                  />
                </div>

                <div className="border-t border-white/5 pt-4">
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-1.5">Registered Sidecar Service</label>
                  <div className="flex gap-4 mb-3">
                    <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                      <input
                        type="radio"
                        name="serviceType"
                        checked={newProject.serviceType === "port"}
                        onChange={() => setNewProject(prev => ({ ...prev, serviceType: "port" }))}
                        className="accent-purple-500"
                      />
                      Listen Port Check
                    </label>
                    <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                      <input
                        type="radio"
                        name="serviceType"
                        checked={newProject.serviceType === "process"}
                        onChange={() => setNewProject(prev => ({ ...prev, serviceType: "process" }))}
                        className="accent-purple-500"
                      />
                      Process Name Check
                    </label>
                  </div>

                  {newProject.serviceType === "port" ? (
                    <input
                      type="number"
                      placeholder="e.g. 3000"
                      value={newProject.servicePort}
                      onChange={(e) => setNewProject(prev => ({ ...prev, servicePort: e.target.value }))}
                      className="w-full px-4 py-2.5 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                    />
                  ) : (
                    <input
                      type="text"
                      placeholder="e.g. node.exe"
                      value={newProject.serviceProcess}
                      onChange={(e) => setNewProject(prev => ({ ...prev, serviceProcess: e.target.value }))}
                      className="w-full px-4 py-2.5 bg-black/40 border border-white/5 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50"
                    />
                  )}
                </div>

                <div className="flex gap-3 justify-end pt-4 border-t border-white/5">
                  <button
                    type="button"
                    onClick={() => setShowAddProjectModal(false)}
                    className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 rounded-xl text-sm font-semibold transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-purple-600/10 hover:shadow-purple-600/25 transition"
                  >
                    Save Project Card
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
