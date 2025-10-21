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
            
            # Quick health check
            self.quick_health_check()
        else:
            self.device_connected = False
            self.connection_status.config(text="No device found", style='Error.TLabel')
            self.log_message("No Android device detected. Please connect your device and enable USB debugging.", "warning")
            
            # Disable monitoring button
            self.monitor_button.config(state='disabled')
            self.analyze_button.config(state='disabled')
    
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
        self.log_message("Starting crash monitoring...", "success")
        
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