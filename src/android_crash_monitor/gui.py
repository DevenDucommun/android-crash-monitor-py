#!/usr/bin/env python3
"""
Simple GUI wrapper for Android Crash Monitor
Designed for non-technical users who prefer graphical interfaces
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Import our new modules
from .plain_language import PlainLanguageExplainer, convert_technical_report_to_plain_language
from .auto_fix import AutoFixManager, create_simple_auto_fixer, quick_device_cleanup

class AndroidCrashMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Android Crash Monitor - Simple Mode")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.monitoring = False
        self.monitoring_thread = None
        self.device_connected = False
        
        # Real-time analysis
        self.realtime_analyzer = None
        self.realtime_update_timer = None
        
        # Predictive analytics
        self.predictive_analyzer = None
        self.prediction_window = None
        
        # Root cause analysis
        self.rca_analyzer = None
        self.rca_window = None
        
        # Style configuration
        style = ttk.Style()
        style.configure('Success.TLabel', foreground='green')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Large.TButton', font=('Arial', 12, 'bold'))
        
        self.create_widgets()
        self.check_initial_status()
    
    def create_widgets(self):
        """Create the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Android Device Health Monitor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Device Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Device connection status
        ttk.Label(status_frame, text="Device Connection:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.connection_status = ttk.Label(status_frame, text="Checking...", style='Warning.TLabel')
        self.connection_status.grid(row=0, column=1, sticky=tk.W)
        
        # Device health status
        ttk.Label(status_frame, text="Device Health:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.health_status = ttk.Label(status_frame, text="Unknown", style='Warning.TLabel')
        self.health_status.grid(row=1, column=1, sticky=tk.W)
        
        # Monitoring status
        ttk.Label(status_frame, text="Monitoring:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.monitoring_status = ttk.Label(status_frame, text="Stopped", style='Warning.TLabel')
        self.monitoring_status.grid(row=2, column=1, sticky=tk.W)
        
        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Main action buttons
        self.setup_button = ttk.Button(button_frame, text="🔧 Setup Device", 
                                      command=self.setup_device, style='Large.TButton')
        self.setup_button.pack(side=tk.LEFT, padx=5)
        
        self.monitor_button = ttk.Button(button_frame, text="▶️ Start Monitoring", 
                                        command=self.toggle_monitoring, style='Large.TButton')
        self.monitor_button.pack(side=tk.LEFT, padx=5)
        
        self.analyze_button = ttk.Button(button_frame, text="🔍 Analyze Issues", 
                                        command=self.analyze_issues, style='Large.TButton')
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.autofix_button = ttk.Button(button_frame, text="🔧 Quick Fix", 
                                        command=self.quick_fix, style='Large.TButton')
        self.autofix_button.pack(side=tk.LEFT, padx=5)
        
        self.predict_button = ttk.Button(button_frame, text="🔮 Predictions", 
                                        command=self.show_predictions, style='Large.TButton')
        self.predict_button.pack(side=tk.LEFT, padx=5)
        
        self.rca_button = ttk.Button(button_frame, text="🔬 Root Cause", 
                                     command=self.show_root_cause_analysis, style='Large.TButton')
        self.rca_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=1)
        
        # Log output area
        log_frame = ttk.LabelFrame(main_frame, text="Status & Results", padding="5")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom buttons frame
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(bottom_frame, text="📄 Save Report", 
                  command=self.save_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🔄 Refresh Status", 
                  command=self.check_initial_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="❌ Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🧪 Test Alert", 
                  command=self._simulate_crash_for_testing).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="❓ Help", 
                  command=self.show_help).pack(side=tk.RIGHT, padx=5)
    
    def log_message(self, message, level="info"):
        """Add a message to the log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "error":
            prefix = "❌ ERROR"
        elif level == "warning":
            prefix = "⚠️  WARNING"
        elif level == "success":
            prefix = "✅ SUCCESS"
        else:
            prefix = "ℹ️  INFO"
        
        full_message = f"[{timestamp}] {prefix}: {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_progress(self, text, show_spinner=False):
        """Update the progress indicator"""
        self.progress_label.config(text=text)
        if show_spinner:
            self.progress.start()
        else:
            self.progress.stop()
        self.root.update()
    
    def run_command(self, command, description="Running command"):
        """Run a command and show progress"""
        self.update_progress(f"{description}...", True)
        self.log_message(f"Running: {description}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=30)
            
            self.update_progress("Ready", False)
            
            if result.returncode == 0:
                self.log_message(f"{description} completed successfully", "success")
                return result.stdout
            else:
                # Don't log stderr for common failures (like missing commands)
                if "not found" in result.stderr or "command not found" in result.stderr:
                    self.log_message(f"{description}: Command not available", "warning")
                else:
                    self.log_message(f"{description} failed: {result.stderr}", "error")
                return None
        except subprocess.TimeoutExpired:
            self.update_progress("Ready", False)
            self.log_message(f"{description} timed out", "error")
            return None
        except FileNotFoundError:
            self.update_progress("Ready", False)
            self.log_message(f"{description}: Command not found", "warning")
            return None
        except Exception as e:
            self.update_progress("Ready", False)
            self.log_message(f"{description} error: {str(e)}", "error")
            return None
    
    def check_initial_status(self):
        """Check device connection and system status"""
        self.log_message("Checking device connection...")
        
        # Check if ADB is available
        adb_result = self.run_command("adb version", "Checking ADB installation")
        if not adb_result:
            self.connection_status.config(text="Setup Required", style='Warning.TLabel')
            self.health_status.config(text="Setup Required", style='Warning.TLabel')
            self.log_message("ADB not found. Click 'Setup Device' to install required tools.", "warning")
            
            # Disable buttons that require ADB
            self.monitor_button.config(state='disabled')
            self.analyze_button.config(state='disabled')
            self.autofix_button.config(state='disabled')
            self.predict_button.config(state='disabled')
            self.rca_button.config(state='disabled')
            return
        
        # Check for connected devices
        devices_result = self.run_command("adb devices", "Checking connected devices")
        if devices_result and "device" in devices_result:
            self.device_connected = True
            self.connection_status.config(text="Connected ✅", style='Success.TLabel')
            self.log_message("Android device found and connected", "success")
            
            # Enable monitoring button
            self.monitor_button.config(state='normal')
            self.analyze_button.config(state='normal')
            self.predict_button.config(state='normal')
            self.rca_button.config(state='normal')
            
            # Quick health check
            self.quick_health_check()
        else:
            self.device_connected = False
            self.connection_status.config(text="No device found", style='Error.TLabel')
            self.log_message("No Android device detected. Please connect your device and enable USB debugging.", "warning")
            
            # Disable monitoring button
            self.monitor_button.config(state='disabled')
            self.analyze_button.config(state='disabled')
            self.predict_button.config(state='disabled')
            self.rca_button.config(state='disabled')
    
    def quick_health_check(self):
        """Perform a quick health assessment"""
        self.log_message("Performing quick health check...")
        
        # Check if device is responsive
        result = self.run_command("adb shell echo 'ping'", "Testing device responsiveness")
        if result and "ping" in result:
            self.health_status.config(text="Good ✅", style='Success.TLabel')
            self.log_message("Device is responsive and healthy", "success")
        else:
            self.health_status.config(text="Issues detected ⚠️", style='Warning.TLabel')
            self.log_message("Device may have responsiveness issues", "warning")
    
    def setup_device(self):
        """Run the setup wizard"""
        self.log_message("Starting device setup wizard...")
        
        def setup_thread():
            # Try to run the setup command
            if os.path.exists("acm"):
                result = self.run_command("python -m android_crash_monitor.cli setup", 
                                        "Running setup wizard")
            else:
                result = self.run_command("./start.sh", "Running setup script")
            
            if result:
                self.log_message("Setup completed successfully!", "success")
                # Recheck status
                self.root.after(1000, self.check_initial_status)
            else:
                self.log_message("Setup encountered some issues. Please check the output above.", "warning")
        
        # Run setup in background thread
        threading.Thread(target=setup_thread, daemon=True).start()
    
    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        if not self.device_connected:
            messagebox.showerror("Error", "No device connected. Please setup your device first.")
            return
        
        self.monitoring = True
        self.monitor_button.config(text="⏹️ Stop Monitoring")
        self.monitoring_status.config(text="Active 🔴", style='Success.TLabel')
        self.log_message("Starting crash monitoring with real-time analysis...", "success")
        
        # Start real-time analyzer
        self._start_realtime_analysis()
        
        def monitor_thread():
            try:
                # Run monitoring command
                if os.path.exists("src/android_crash_monitor"):
                    cmd = "python -m android_crash_monitor.cli monitor"
                else:
                    cmd = "./start.sh"
                
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                for line in process.stdout:
                    if not self.monitoring:  # Check if we should stop
                        process.terminate()
                        break
                    
                    # Update GUI with monitoring output
                    self.root.after(0, lambda l=line.strip(): self.log_message(l) if l else None)
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Monitoring error: {str(e)}", "error"))
            finally:
                # Reset monitoring state
                self.root.after(0, self.stop_monitoring)
        
        self.monitoring_thread = threading.Thread(target=monitor_thread, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.monitor_button.config(text="▶️ Start Monitoring")
        self.monitoring_status.config(text="Stopped", style='Warning.TLabel')
        self.log_message("Monitoring stopped", "info")
        
        # Stop real-time analyzer
        self._stop_realtime_analysis()
        
        # Automatically offer analysis
        if messagebox.askyesno("Analysis", "Monitoring stopped. Would you like to analyze the collected data?"):
            self.analyze_issues()
    
    def analyze_issues(self):
        """Run enhanced crash analysis"""
        if not self.device_connected:
            messagebox.showerror("Error", "No device connected. Please setup your device first.")
            return
        
        self.log_message("Starting enhanced crash analysis...")
        
        def analyze_thread():
            try:
                # Try to use enhanced analysis if available
                from .analysis.enhanced_analyzer import EnhancedCrashAnalyzer
                from pathlib import Path
                
                # Create analyzer with logs directory
                logs_dir = Path.cwd() / "logs"
                if not logs_dir.exists():
                    logs_dir.mkdir(exist_ok=True)
                
                analyzer = EnhancedCrashAnalyzer(logs_dir)
                result = analyzer.analyze_comprehensive()
                
                # Display enhanced results in GUI
                self.root.after(0, lambda: self._display_enhanced_analysis(result))
                
            except ImportError as e:
                # Fallback to traditional analysis
                self.root.after(0, lambda: self.log_message("Using traditional analysis (enhanced features not available)", "warning"))
                if os.path.exists("src/android_crash_monitor"):
                    result = self.run_command("python -m android_crash_monitor.cli analyze --summary", 
                                            "Analyzing crash patterns")
                else:
                    result = self.run_command("python analyze_recent_crash.py", 
                                            "Running crash analysis")
                
                if result:
                    self.root.after(0, lambda: self.log_message("Analysis completed! Check results above.", "success"))
                else:
                    self.root.after(0, lambda: self.log_message("Analysis completed with some warnings.", "warning"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Enhanced analysis error: {str(e)}", "error"))
                # Fallback to traditional analysis
                if os.path.exists("src/android_crash_monitor"):
                    result = self.run_command("python -m android_crash_monitor.cli analyze --summary", 
                                            "Analyzing crash patterns (fallback)")
                else:
                    result = self.run_command("python analyze_recent_crash.py", 
                                            "Running crash analysis (fallback)")
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def save_report(self):
        """Save the current log to a file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Report As..."
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"Report saved to {filename}", "success")
            except Exception as e:
                self.log_message(f"Error saving report: {str(e)}", "error")
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log cleared")
    
    def quick_fix(self):
        """Apply quick fixes to common problems"""
        if not self.device_connected:
            messagebox.showerror("Error", "No device connected. Please setup your device first.")
            return
        
        # Ask user for confirmation
        if not messagebox.askyesno("Quick Fix", 
                                  "Apply safe automatic fixes to common problems?\n\n"
                                  "This will:\n"
                                  "• Clear app caches\n"
                                  "• Stop problematic apps\n"
                                  "• Free up storage space\n\n"
                                  "No personal data will be deleted."):
            return
        
        self.log_message("Starting automatic fixes...", "info")
        
        def fix_thread():
            try:
                # Apply quick fixes
                results = quick_device_cleanup()
                
                # Create auto-fixer for report generation
                fixer = create_simple_auto_fixer()
                report = fixer.create_fix_report(results)
                
                # Display results in the GUI
                self.root.after(0, lambda: self.display_fix_results(report, results))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Auto-fix error: {str(e)}", "error"))
        
        threading.Thread(target=fix_thread, daemon=True).start()
    
    def display_fix_results(self, report: str, results: dict):
        """Display fix results to user"""
        successful_fixes = sum(1 for result in results.values() if result.success)
        total_fixes = len(results)
        
        if successful_fixes > 0:
            self.log_message(f"Quick fixes completed: {successful_fixes}/{total_fixes} successful", "success")
            
            # Show detailed report in a popup
            result_window = tk.Toplevel(self.root)
            result_window.title("Quick Fix Results")
            result_window.geometry("600x400")
            
            # Create scrollable text widget
            text_frame = ttk.Frame(result_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            result_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
            result_text.pack(fill=tk.BOTH, expand=True)
            
            # Insert the report
            result_text.insert(tk.END, report)
            result_text.config(state=tk.DISABLED)
            
            # Add close button
            button_frame = ttk.Frame(result_window)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Close", 
                      command=result_window.destroy).pack()
            
            # Recommend restart
            if successful_fixes > 0:
                if messagebox.askyesno("Restart Recommended", 
                                      "Fixes applied successfully!\n\n"
                                      "Restart your device now for best results?"):
                    self.log_message("User chose to restart device", "info")
        else:
            self.log_message("No fixes could be applied automatically", "warning")
            messagebox.showinfo("Quick Fix Results", 
                               "No automatic fixes were applied.\n\n"
                               "Your device may not have common issues, or "
                               "manual troubleshooting may be needed.")
    
    def _display_enhanced_analysis(self, result):
        """Display enhanced analysis results in a popup window"""
        try:
            # Create analysis results window
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("Enhanced Analysis Results")
            analysis_window.geometry("900x700")
            
            # Create notebook for tabbed interface
            notebook = ttk.Notebook(analysis_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Summary tab
            summary_frame = ttk.Frame(notebook)
            notebook.add(summary_frame, text="📊 Summary")
            
            summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD)
            summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Insert summary content
            summary_content = f"""
🎯 ENHANCED ANALYSIS RESULTS
{"="*50}

Analysis Confidence: {result.overall_confidence:.1%}
Quality Score: {result.analysis_quality_score:.1%}
Crashes Analyzed: {result.total_crashes_analyzed}
Analysis Time: {result.analysis_duration_seconds:.2f} seconds

{result.user_friendly_summary}

📋 PRIORITY RECOMMENDATIONS:
{"="*30}

"""
            
            for i, rec in enumerate(result.detailed_recommendations, 1):
                summary_content += f"{i}. {rec}\n"
            
            summary_text.insert(tk.END, summary_content)
            summary_text.config(state=tk.DISABLED)
            
            # Enhanced Patterns tab
            if result.enhanced_patterns:
                patterns_frame = ttk.Frame(notebook)
                notebook.add(patterns_frame, text="🔍 Enhanced Patterns")
                
                patterns_text = scrolledtext.ScrolledText(patterns_frame, wrap=tk.WORD)
                patterns_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                patterns_content = "ENHANCED STATISTICAL PATTERNS\n" + "="*40 + "\n\n"
                
                for i, pattern in enumerate(result.enhanced_patterns, 1):
                    severity_icon = {
                        "LOW": "🟢",
                        "MEDIUM": "🟡", 
                        "HIGH": "🟠",
                        "CRITICAL": "🔴"
                    }.get(pattern.severity.name, "⚪")
                    
                    patterns_content += f"""{i}. {severity_icon} {pattern.name.upper()}
   Confidence: {pattern.confidence_score:.1%} | Urgency: {pattern.urgency_level}/10
   Frequency: {pattern.frequency} occurrences
   
   📝 Description: {pattern.description}
   
   🔍 Evidence:
"""
                    for evidence in pattern.evidence:
                        patterns_content += f"   • {evidence}\n"
                    
                    patterns_content += "\n   💡 Recommended Actions:\n"
                    for action in pattern.recommended_actions:
                        patterns_content += f"   • {action}\n"
                    
                    patterns_content += "\n" + "-"*60 + "\n\n"
                
                patterns_text.insert(tk.END, patterns_content)
                patterns_text.config(state=tk.DISABLED)
            
            # System Health tab
            health_frame = ttk.Frame(notebook)
            notebook.add(health_frame, text="💻 System Health")
            
            health_text = scrolledtext.ScrolledText(health_frame, wrap=tk.WORD)
            health_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            health_icon = {
                "STABLE": "🟢",
                "DEGRADED": "🟡",
                "UNSTABLE": "🟠", 
                "CRITICAL": "🔴"
            }.get(result.system_health.status, "⚪")
            
            health_content = f"""
SYSTEM HEALTH ASSESSMENT
{"="*30}

{health_icon} Status: {result.system_health.status}
📊 Confidence: {result.system_health.confidence:.1%}

📝 Summary:
{result.system_health.summary}

⚠️  Risk Assessment:
• Cascade Risk: {'YES' if result.system_health.cascade_risk else 'NO'}
• Reboot Risk: {'YES' if result.system_health.reboot_risk else 'NO'}

Primary Issues Detected: {len(result.system_health.primary_issues)}
"""
            
            if result.system_health.primary_issues:
                health_content += "\n🔍 Top Issues:\n"
                for issue in result.system_health.primary_issues:
                    health_content += f"• {issue.description}\n"
            
            health_text.insert(tk.END, health_content)
            health_text.config(state=tk.DISABLED)
            
            # Full Report tab
            report_frame = ttk.Frame(notebook)
            notebook.add(report_frame, text="📄 Full Report")
            
            report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD)
            report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Generate full plain language report
            try:
                from .analysis.enhanced_analyzer import EnhancedCrashAnalyzer
                logs_dir = Path.cwd() / "logs"
                analyzer = EnhancedCrashAnalyzer(logs_dir)
                full_report = analyzer.get_plain_language_report()
                report_text.insert(tk.END, full_report)
            except Exception as e:
                report_text.insert(tk.END, f"Error generating full report: {e}")
            
            report_text.config(state=tk.DISABLED)
            
            # Add buttons at bottom
            button_frame = ttk.Frame(analysis_window)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Save Analysis Report", 
                      command=lambda: self._save_enhanced_analysis(result)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", 
                      command=analysis_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Log success
            self.log_message(f"Enhanced analysis completed! Found {len(result.enhanced_patterns)} patterns with {result.overall_confidence:.1%} confidence.", "success")
            
        except Exception as e:
            self.log_message(f"Error displaying enhanced analysis: {str(e)}", "error")
    
    def _save_enhanced_analysis(self, result):
        """Save enhanced analysis results to file"""
        try:
            from tkinter import filedialog
            from pathlib import Path
            
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Enhanced Analysis Report"
            )
            
            if filename:
                filepath = Path(filename)
                
                if filepath.suffix.lower() == '.json':
                    # Save as JSON
                    from .analysis.enhanced_analyzer import EnhancedCrashAnalyzer
                    logs_dir = Path.cwd() / "logs"
                    analyzer = EnhancedCrashAnalyzer(logs_dir)
                    success = analyzer.export_analysis_json(filepath)
                    
                    if success:
                        self.log_message(f"Enhanced analysis saved to {filename}", "success")
                    else:
                        self.log_message(f"Error saving analysis to {filename}", "error")
                else:
                    # Save as plain text report
                    from .analysis.enhanced_analyzer import EnhancedCrashAnalyzer
                    logs_dir = Path.cwd() / "logs"
                    analyzer = EnhancedCrashAnalyzer(logs_dir)
                    report = analyzer.get_plain_language_report()
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report)
                    
                    self.log_message(f"Analysis report saved to {filename}", "success")
        
        except Exception as e:
            self.log_message(f"Error saving analysis: {str(e)}", "error")
    
    def _start_realtime_analysis(self):
        """Start real-time pattern analysis during monitoring"""
        try:
            from .analysis.realtime_analyzer import RealtimePatternAnalyzer, RealTimeAlert
            
            # Create real-time analyzer with alert callback
            self.realtime_analyzer = RealtimePatternAnalyzer(
                buffer_size=200,
                analysis_window_minutes=15,
                alert_callback=self._handle_realtime_alert
            )
            
            # Start real-time analysis
            if self.realtime_analyzer.start_realtime_analysis():
                self.log_message("Real-time pattern analysis started", "success")
                
                # Start GUI update timer
                self._start_realtime_gui_updates()
            else:
                self.log_message("Failed to start real-time analysis", "warning")
                
        except ImportError:
            self.log_message("Real-time analysis not available - using basic monitoring", "warning")
        except Exception as e:
            self.log_message(f"Error starting real-time analysis: {e}", "error")
    
    def _stop_realtime_analysis(self):
        """Stop real-time pattern analysis"""
        if self.realtime_analyzer:
            try:
                self.realtime_analyzer.stop_realtime_analysis()
                self.log_message("Real-time analysis stopped", "info")
            except Exception as e:
                self.log_message(f"Error stopping real-time analysis: {e}", "error")
            
            self.realtime_analyzer = None
        
        # Stop GUI updates
        if self.realtime_update_timer:
            self.root.after_cancel(self.realtime_update_timer)
            self.realtime_update_timer = None
    
    def _start_realtime_gui_updates(self):
        """Start periodic GUI updates for real-time data"""
        self._update_realtime_display()
        # Schedule next update in 2 seconds
        self.realtime_update_timer = self.root.after(2000, self._start_realtime_gui_updates)
    
    def _update_realtime_display(self):
        """Update GUI with real-time statistics"""
        if not self.realtime_analyzer or not self.monitoring:
            return
        
        try:
            stats = self.realtime_analyzer.get_realtime_stats()
            active_patterns = self.realtime_analyzer.get_active_patterns()
            
            # Update status with real-time stats
            status_text = f"Active \ud83d\udd34 | {stats.total_crashes} crashes | {len(active_patterns)} patterns"
            if stats.crashes_last_minute > 0:
                status_text += f" | {stats.crashes_last_minute}/min"
            
            self.monitoring_status.config(text=status_text)
            
            # Log significant events
            if stats.crashes_last_minute >= 3:
                self.log_message(f"\u26a0\ufe0f High activity: {stats.crashes_last_minute} crashes in last minute", "warning")
            
            if len(active_patterns) > 0:
                highest_confidence = max(p.confidence_score for p in active_patterns)
                if highest_confidence >= 0.8:
                    pattern_name = next(p.name for p in active_patterns if p.confidence_score == highest_confidence)
                    self.log_message(f"\ud83c\udfa2 High confidence pattern: {pattern_name} ({highest_confidence:.1%})", "info")
            
        except Exception as e:
            self.log_message(f"Error updating real-time display: {e}", "error")
    
    def _handle_realtime_alert(self, alert):
        """Handle real-time alerts"""
        try:
            # Log alert to GUI
            if alert.level.value >= 4:  # Critical or Emergency
                level_text = "error"
                alert_icon = "\ud83d\udea8"
            elif alert.level.value >= 3:  # High
                level_text = "warning"
                alert_icon = "\u26a0\ufe0f"
            else:
                level_text = "info"
                alert_icon = "\ud83d\udd14"
            
            message = f"{alert_icon} ALERT: {alert.message}"
            self.log_message(message, level_text)
            
            # Show recommended action
            if alert.recommended_action and alert.level.value >= 3:
                self.log_message(f"\u27a1\ufe0f Recommended: {alert.recommended_action}", "info")
            
            # For critical alerts, show popup
            if alert.level.value >= 4 and not alert.auto_dismissible:
                self.root.after(0, lambda: self._show_critical_alert_popup(alert))
                
        except Exception as e:
            print(f"Error handling real-time alert: {e}")
    
    def _show_critical_alert_popup(self, alert):
        """Show popup for critical alerts"""
        try:
            # Create alert popup
            alert_window = tk.Toplevel(self.root)
            alert_window.title("Critical Alert")
            alert_window.geometry("500x300")
            alert_window.configure(bg="#ffebee")  # Light red background
            
            # Make it always on top
            alert_window.attributes('-topmost', True)
            
            # Alert content frame
            content_frame = ttk.Frame(alert_window, padding="20")
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Alert title
            title_label = ttk.Label(content_frame, 
                                   text=f"\ud83d\udea8 {alert.level.name} ALERT",
                                   font=('Arial', 16, 'bold'))
            title_label.pack(pady=(0, 10))
            
            # Alert message
            message_label = ttk.Label(content_frame, 
                                     text=alert.message,
                                     font=('Arial', 12),
                                     wraplength=450)
            message_label.pack(pady=(0, 15))
            
            # Confidence and urgency
            details_label = ttk.Label(content_frame,
                                     text=f"Confidence: {alert.confidence:.1%} | Urgency: {alert.urgency}/10",
                                     font=('Arial', 10))
            details_label.pack(pady=(0, 15))
            
            # Recommended action
            if alert.recommended_action:
                action_label = ttk.Label(content_frame,
                                        text=f"Recommended Action:\n{alert.recommended_action}",
                                        font=('Arial', 11, 'bold'),
                                        wraplength=450)
                action_label.pack(pady=(0, 20))
            
            # Buttons
            button_frame = ttk.Frame(content_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Acknowledge", 
                      command=alert_window.destroy).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Stop Monitoring", 
                      command=lambda: (alert_window.destroy(), self.stop_monitoring())).pack(side=tk.LEFT, padx=5)
            
            # Flash the window to get attention
            def flash_window(count=6):
                if count > 0:
                    try:
                        current_color = alert_window.cget('bg')
                        new_color = '#ffcdd2' if current_color == '#ffebee' else '#ffebee'
                        alert_window.configure(bg=new_color)
                        alert_window.after(200, lambda: flash_window(count-1))
                    except tk.TclError:
                        pass  # Window might be closed
            
            flash_window()
            
        except Exception as e:
            print(f"Error showing critical alert popup: {e}")
    
    def _simulate_crash_for_testing(self):
        """Simulate a crash for testing real-time analysis"""
        if self.realtime_analyzer:
            import time
            test_crash = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'TestApp',
                'description': 'OutOfMemoryError: Java heap space exceeded',
                'title': 'Test Memory Crash',
                'related_logs': [{'message': 'Process killed low memory', 'level': 'ERROR'}]
            }
            self.realtime_analyzer.add_crash(test_crash)
            self.log_message("🧪 Test crash injected for real-time analysis", "info")
            
            # Also add to predictive analyzer if available
            if self.predictive_analyzer:
                self.predictive_analyzer.add_crash(test_crash)
    
    def show_predictions(self):
        """Show crash prediction dashboard"""
        if not self.device_connected:
            messagebox.showerror("Error", "No device connected. Please setup your device first.")
            return
        
        # Close existing prediction window if open
        if self.prediction_window and self.prediction_window.winfo_exists():
            self.prediction_window.lift()
            return
        
        self.log_message("Generating crash predictions...")
        
        def predict_thread():
            try:
                from .analysis.predictive_analytics import PredictiveCrashAnalyzer, RiskLevel
                
                # Initialize predictive analyzer if needed
                if not self.predictive_analyzer:
                    self.predictive_analyzer = PredictiveCrashAnalyzer()
                    
                    # Load crashes from real-time analyzer if available
                    if self.realtime_analyzer:
                        for crash in list(self.realtime_analyzer.crash_buffer):
                            self.predictive_analyzer.add_crash(crash)
                
                # Generate predictions
                prediction = self.predictive_analyzer.predict_crashes(prediction_window=60)
                
                # Show prediction dashboard
                self.root.after(0, lambda: self._show_prediction_dashboard(prediction))
                
            except ImportError:
                self.root.after(0, lambda: self.log_message("Predictive analytics not available", "warning"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Prediction error: {e}", "error"))
        
        threading.Thread(target=predict_thread, daemon=True).start()
    
    def _show_prediction_dashboard(self, prediction):
        """Display prediction dashboard window"""
        try:
            from .analysis.predictive_analytics import RiskLevel, TrendDirection
            
            # Create prediction window
            self.prediction_window = tk.Toplevel(self.root)
            self.prediction_window.title("🔮 Crash Prediction Dashboard")
            self.prediction_window.geometry("700x600")
            
            # Set background color based on risk level
            risk_colors = {
                RiskLevel.VERY_LOW: '#e8f5e9',    # Light green
                RiskLevel.LOW: '#fff9c4',          # Light yellow
                RiskLevel.MEDIUM: '#ffe0b2',       # Light orange
                RiskLevel.HIGH: '#ffccbc',         # Light red
                RiskLevel.CRITICAL: '#ffebee'      # Bright red
            }
            self.prediction_window.configure(bg=risk_colors.get(prediction.risk_level, '#ffffff'))
            
            # Main frame
            main_frame = ttk.Frame(self.prediction_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title with risk level
            risk_icons = {
                RiskLevel.VERY_LOW: '🟢',
                RiskLevel.LOW: '🟡',
                RiskLevel.MEDIUM: '🟠',
                RiskLevel.HIGH: '🔴',
                RiskLevel.CRITICAL: '🚨'
            }
            title_text = f"{risk_icons.get(prediction.risk_level, '🔵')} {prediction.risk_level.name} RISK"
            title_label = ttk.Label(main_frame, text=title_text, font=('Arial', 20, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Risk score and confidence
            score_frame = ttk.Frame(main_frame)
            score_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(score_frame, text=f"Risk Score: {prediction.risk_score:.1%}",
                     font=('Arial', 14)).pack(side=tk.LEFT, padx=10)
            ttk.Label(score_frame, text=f"Confidence: {prediction.confidence:.1%}",
                     font=('Arial', 14)).pack(side=tk.LEFT, padx=10)
            ttk.Label(score_frame, text=f"Urgency: {prediction.urgency_level}/10",
                     font=('Arial', 14)).pack(side=tk.LEFT, padx=10)
            
            # Prediction
            pred_frame = ttk.LabelFrame(main_frame, text="Next Hour Prediction", padding="15")
            pred_frame.pack(fill=tk.X, pady=(0, 15))
            
            pred_text = f"📊 Predicted crashes: {prediction.predicted_crash_count}\n"
            pred_text += f"Range: {prediction.predicted_crash_range[0]}-{prediction.predicted_crash_range[1]} crashes\n"
            
            trend_icons = {
                TrendDirection.DECLINING: '📉',
                TrendDirection.STABLE: '➡️',
                TrendDirection.RISING: '📈',
                TrendDirection.ACCELERATING: '🚀'
            }
            pred_text += f"\nTrend: {trend_icons.get(prediction.trend, '')} {prediction.trend.name}"
            if prediction.trend_strength > 0:
                pred_text += f" (strength: {prediction.trend_strength:.1%})"
            
            ttk.Label(pred_frame, text=pred_text, font=('Arial', 12)).pack()
            
            # Risk factors
            if prediction.primary_risk_factors:
                factors_frame = ttk.LabelFrame(main_frame, text="Primary Risk Factors", padding="15")
                factors_frame.pack(fill=tk.X, pady=(0, 15))
                
                for factor in prediction.primary_risk_factors:
                    score = prediction.risk_factor_scores.get(factor, 0)
                    factor_text = f"• {factor}: {score:.1%}"
                    ttk.Label(factors_frame, text=factor_text, font=('Arial', 11)).pack(anchor=tk.W, pady=2)
            
            # Recommendations
            if prediction.recommended_actions:
                rec_frame = ttk.LabelFrame(main_frame, text="💡 Recommendations", padding="15")
                rec_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                
                rec_text = scrolledtext.ScrolledText(rec_frame, wrap=tk.WORD, height=6, font=('Arial', 11))
                rec_text.pack(fill=tk.BOTH, expand=True)
                
                for i, action in enumerate(prediction.recommended_actions, 1):
                    rec_text.insert(tk.END, f"{i}. {action}\n")
                rec_text.config(state='disabled')
            
            # Action buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="🔄 Refresh Prediction", 
                      command=self.show_predictions).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="📊 Analyze Now", 
                      command=lambda: (self.prediction_window.destroy(), self.analyze_issues())).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Close", 
                      command=self.prediction_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Timestamp
            time_label = ttk.Label(main_frame, 
                                  text=f"Generated: {prediction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                                  font=('Arial', 9))
            time_label.pack(pady=(10, 0))
            
            self.log_message(f"Prediction dashboard opened - {prediction.risk_level.name} risk detected", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show prediction dashboard: {e}")
            self.log_message(f"Dashboard error: {e}", "error")
    
    def show_root_cause_analysis(self):
        """Show root cause analysis dashboard"""
        if not self.device_connected:
            messagebox.showerror("Error", "No device connected. Please setup your device first.")
            return
        
        # Close existing RCA window if open
        if self.rca_window and self.rca_window.winfo_exists():
            self.rca_window.lift()
            return
        
        self.log_message("Running root cause analysis...")
        
        def rca_thread():
            try:
                from .analysis.root_cause_analyzer import RootCauseAnalyzer
                
                # Initialize RCA analyzer if needed
                if not self.rca_analyzer:
                    self.rca_analyzer = RootCauseAnalyzer()
                
                # Get crashes from real-time analyzer or create test data
                crashes = []
                if self.realtime_analyzer and len(self.realtime_analyzer.crash_buffer) > 0:
                    crashes = list(self.realtime_analyzer.crash_buffer)
                else:
                    # If no crashes, inform user
                    self.root.after(0, lambda: messagebox.showinfo(
                        "No Crash Data",
                        "No crash data available for analysis.\n\n"
                        "Start monitoring to collect crash data, or the test alert button to inject sample crashes."
                    ))
                    return
                
                # Run RCA
                result = self.rca_analyzer.analyze(crashes)
                
                # Show RCA dashboard
                self.root.after(0, lambda: self._show_rca_dashboard(result))
                
            except ImportError:
                self.root.after(0, lambda: self.log_message("Root cause analysis not available", "warning"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"RCA error: {e}", "error"))
        
        threading.Thread(target=rca_thread, daemon=True).start()
    
    def _show_rca_dashboard(self, rca_result):
        """Display RCA dashboard window"""
        try:
            from .analysis.root_cause_analyzer import CauseType, FailureMode
            
            # Create RCA window
            self.rca_window = tk.Toplevel(self.root)
            self.rca_window.title("🔬 Root Cause Analysis")
            self.rca_window.geometry("900x700")
            
            # Main container with scrollbar
            main_canvas = tk.Canvas(self.rca_window)
            scrollbar = ttk.Scrollbar(self.rca_window, orient="vertical", command=main_canvas.yview)
            scrollable_frame = ttk.Frame(main_canvas, padding="20")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            )
            
            main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            main_canvas.configure(yscrollcommand=scrollbar.set)
            
            main_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Title
            title_label = ttk.Label(scrollable_frame, 
                                   text="🔬 Root Cause Analysis Results",
                                   font=('Arial', 18, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Analysis info
            info_frame = ttk.Frame(scrollable_frame)
            info_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(info_frame, text=f"Analysis ID: {rca_result.analysis_id}",
                     font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
            ttk.Label(info_frame, text=f"Confidence: {rca_result.overall_confidence:.1%}",
                     font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
            
            # Primary Root Causes
            if rca_result.primary_root_causes:
                causes_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Primary Root Causes", padding="15")
                causes_frame.pack(fill=tk.X, pady=(0, 15))
                
                for i, cause in enumerate(rca_result.primary_root_causes, 1):
                    cause_container = ttk.Frame(causes_frame)
                    cause_container.pack(fill=tk.X, pady=5)
                    
                    # Cause header
                    header_text = f"{i}. {cause['cause']} (Confidence: {cause['confidence']:.1%})"
                    ttk.Label(cause_container, text=header_text, font=('Arial', 11, 'bold')).pack(anchor=tk.W)
                    
                    # Description
                    desc_text = cause['description'][:100] + "..." if len(cause['description']) > 100 else cause['description']
                    ttk.Label(cause_container, text=f"   {desc_text}", font=('Arial', 10)).pack(anchor=tk.W, padx=20)
                    
                    # Frequency
                    ttk.Label(cause_container, text=f"   Frequency: {cause['frequency']} occurrences",
                             font=('Arial', 9)).pack(anchor=tk.W, padx=20)
            
            # Contributing Factors
            if rca_result.contributing_factors:
                factors_frame = ttk.LabelFrame(scrollable_frame, text="⚠️  Contributing Factors", padding="15")
                factors_frame.pack(fill=tk.X, pady=(0, 15))
                
                for factor in rca_result.contributing_factors[:5]:
                    factor_text = f"• {factor['factor']} ({factor['component_type']}): "
                    factor_text += f"Health {factor['health_score']:.1%}, {factor['failure_count']} failures"
                    ttk.Label(factors_frame, text=factor_text, font=('Arial', 10)).pack(anchor=tk.W, pady=2)
            
            # Dependencies (show top 5)
            if rca_result.crash_dependencies:
                dep_frame = ttk.LabelFrame(scrollable_frame, text="🔗 Crash Dependencies", padding="15")
                dep_frame.pack(fill=tk.X, pady=(0, 15))
                
                for dep in rca_result.crash_dependencies[:5]:
                    dep_text = f"• {dep.source_crash_id} → {dep.target_crash_id}"
                    dep_text += f" ({dep.dependency_type}, {dep.confidence:.1%}, {dep.time_delta:.1f}s)"
                    ttk.Label(dep_frame, text=dep_text, font=('Arial', 10)).pack(anchor=tk.W, pady=2)
                
                if len(rca_result.crash_dependencies) > 5:
                    ttk.Label(dep_frame, text=f"... and {len(rca_result.crash_dependencies) - 5} more",
                             font=('Arial', 9, 'italic')).pack(anchor=tk.W, pady=2)
            
            # Causal Chains
            if rca_result.causal_chains:
                chains_frame = ttk.LabelFrame(scrollable_frame, text="🔗 Causal Chains", padding="15")
                chains_frame.pack(fill=tk.X, pady=(0, 15))
                
                for i, chain in enumerate(rca_result.causal_chains[:3], 1):
                    chain_container = ttk.Frame(chains_frame)
                    chain_container.pack(fill=tk.X, pady=5)
                    
                    chain_header = f"Chain {i}: {len(chain.events)} events, confidence {chain.confidence:.1%}"
                    if chain.failure_mode:
                        chain_header += f" ({chain.failure_mode.value})"
                    ttk.Label(chain_container, text=chain_header, font=('Arial', 10, 'bold')).pack(anchor=tk.W)
                    
                    # Show event flow
                    for j, event in enumerate(chain.events[:4]):  # Show first 4 events
                        role = event.get('role', 'unknown').upper()
                        crash_id = event.get('crash_id', 'unknown')
                        arrow = " → " if j < len(chain.events) - 1 else ""
                        event_text = f"   {role}: {crash_id}{arrow}"
                        ttk.Label(chain_container, text=event_text, font=('Arial', 9)).pack(anchor=tk.W, padx=20)
            
            # Evidence
            if rca_result.evidence_summary:
                evidence_frame = ttk.LabelFrame(scrollable_frame, text="📋 Evidence", padding="15")
                evidence_frame.pack(fill=tk.X, pady=(0, 15))
                
                for evidence in rca_result.evidence_summary:
                    ttk.Label(evidence_frame, text=f"• {evidence}", font=('Arial', 10)).pack(anchor=tk.W, pady=2)
            
            # Remediation Steps
            if rca_result.remediation_steps:
                remediation_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Remediation Steps", padding="15")
                remediation_frame.pack(fill=tk.X, pady=(0, 15))
                
                for i, step in enumerate(rca_result.remediation_steps, 1):
                    ttk.Label(remediation_frame, text=f"{i}. {step}", font=('Arial', 10)).pack(anchor=tk.W, pady=2)
            
            # Prevention Measures
            if rca_result.prevention_measures:
                prevention_frame = ttk.LabelFrame(scrollable_frame, text="🛡️  Prevention Measures", padding="15")
                prevention_frame.pack(fill=tk.X, pady=(0, 15))
                
                for i, measure in enumerate(rca_result.prevention_measures, 1):
                    ttk.Label(prevention_frame, text=f"{i}. {measure}", font=('Arial', 10)).pack(anchor=tk.W, pady=2)
            
            # Action buttons
            button_frame = ttk.Frame(scrollable_frame)
            button_frame.pack(pady=20)
            
            ttk.Button(button_frame, text="💾 Save Report",
                      command=lambda: self._save_rca_report(rca_result)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Close",
                      command=self.rca_window.destroy).pack(side=tk.LEFT, padx=5)
            
            self.log_message(f"RCA completed - {len(rca_result.primary_root_causes)} root causes identified", "success")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show RCA dashboard: {e}")
            self.log_message(f"RCA dashboard error: {e}", "error")
    
    def _save_rca_report(self, rca_result):
        """Save RCA report to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"rca_{rca_result.analysis_id}.txt",
            title="Save RCA Report As..."
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(f"Root Cause Analysis Report\n")
                    f.write(f"{'=' * 60}\n\n")
                    f.write(f"Analysis ID: {rca_result.analysis_id}\n")
                    f.write(f"Timestamp: {rca_result.timestamp}\n")
                    f.write(f"Overall Confidence: {rca_result.overall_confidence:.1%}\n\n")
                    
                    if rca_result.primary_root_causes:
                        f.write(f"\nPrimary Root Causes:\n")
                        f.write(f"{'-' * 40}\n")
                        for i, cause in enumerate(rca_result.primary_root_causes, 1):
                            f.write(f"{i}. {cause['cause']} (Confidence: {cause['confidence']:.1%})\n")
                            f.write(f"   {cause['description']}\n")
                            f.write(f"   Frequency: {cause['frequency']}\n\n")
                    
                    if rca_result.contributing_factors:
                        f.write(f"\nContributing Factors:\n")
                        f.write(f"{'-' * 40}\n")
                        for factor in rca_result.contributing_factors:
                            f.write(f"- {factor['factor']} ({factor['component_type']})\n")
                            f.write(f"  Health: {factor['health_score']:.1%}, Failures: {factor['failure_count']}\n")
                    
                    if rca_result.remediation_steps:
                        f.write(f"\nRemediation Steps:\n")
                        f.write(f"{'-' * 40}\n")
                        for i, step in enumerate(rca_result.remediation_steps, 1):
                            f.write(f"{i}. {step}\n")
                    
                    if rca_result.prevention_measures:
                        f.write(f"\nPrevention Measures:\n")
                        f.write(f"{'-' * 40}\n")
                        for i, measure in enumerate(rca_result.prevention_measures, 1):
                            f.write(f"{i}. {measure}\n")
                
                self.log_message(f"RCA report saved to {filename}", "success")
            except Exception as e:
                self.log_message(f"Error saving RCA report: {e}", "error")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Android Crash Monitor - Enhanced Mode

How to use:
1. Connect your Android device via USB
2. Click "Setup Device" to install required tools
3. Click "Start Monitoring" to watch for crashes
4. Click "Analyze Issues" to run enhanced statistical analysis
5. Click "Quick Fix" to automatically resolve common problems
6. Use "Save Report" to keep results

Enhanced Features:
- Statistical pattern detection with confidence scoring
- Temporal clustering analysis for burst detection
- Correlation analysis between different crash types
- Cascade failure detection for complex issues
- Plain language explanations with urgency levels

Troubleshooting:
- Make sure USB Debugging is enabled on your device
- Check that your device appears in device manager
- Try a different USB cable if connection fails
- Restart both your device and computer if needed
- Use "Quick Fix" for automatic problem resolution

For more help, visit: https://github.com/DevenDucommun/android-crash-monitor-py
        """
        
        messagebox.showinfo("Help - Android Crash Monitor Enhanced", help_text)

def main():
    """Main entry point for GUI mode"""
    root = tk.Tk()
    app = AndroidCrashMonitorGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is active. Stop monitoring and quit?"):
                app.stop_monitoring()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()