# import os
# import traceback
# from datetime import datetime
# import matplotlib.pyplot as plt
# from matplotlib.figure import Figure
# import matplotlib.table as mplt
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch, cm
# from reportlab.lib import colors
# from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, 
#                               PageBreak, Table, TableStyle, KeepTogether)
# from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from views.visualization_components.plotting_logic import plot_selected_graph

# class EnhancedReportGenerator:
#     """Enhanced report generator with comprehensive features and better organization."""
    
#     def __init__(self, parent):
#         self.parent = parent
#         self.temp_dir = None
#         self.progress_dialog = None

#     def _get_project_info(self):
#         """Get project information from database."""
#         try:
#             if hasattr(self.parent, 'project_id'):
#                 from controllers.database.database_manager import DatabaseManager
#                 db = DatabaseManager()
#                 cursor = db.connection.execute(
#                     "SELECT project_name, location, company, capacity, model_name FROM Projects WHERE project_id = ?",
#                     [self.parent.project_id]
#                 )
#                 row = cursor.fetchone()
#                 db.close()
                
#                 if row:
#                     return {
#                         'name': row[0],
#                         'location': row[1],
#                         'company': row[2],
#                         'capacity': row[3],
#                         'model_name': row[4]
#                     }
#         except Exception as e:
#             print(f"Error getting project info: {e}")
        
#         return {}

#     def generate_report(self):
#         """Generate a comprehensive PDF report with enhanced features and user plot support."""
#         try:
#             if self.parent.data is None or self.parent.data.empty:
#                 self.parent.handle_errors("No data available to generate report.")
#                 return

#             # Show plot selection dialog
#             selected_plots = self._create_plot_selection_dialog()
#             if selected_plots is None:  # User cancelled
#                 return

#             # Setup progress dialog
#             self.progress_dialog = QProgressDialog("Generating report...", "Cancel", 0, 100, self.parent)
#             self.progress_dialog.setWindowModality(Qt.WindowModal)
#             self.progress_dialog.show()
          
#             # Get save location
#             # turbine_id = self.turbine_id or 'Unknown'
#             turbine_id = getattr(self.parent, 'turbine_name', None) or getattr(self.parent, 'windowTitle', lambda: 'Unknown')().split(': ')[-1] if ': ' in getattr(self.parent, 'windowTitle', lambda: 'Unknown')() else 'Unknown'
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             default_filename = f"Wind_Turbine_Report_{turbine_id}_{timestamp}.pdf"
            
#             file_name, _ = QFileDialog.getSaveFileName(
#                 self.parent, "Save Report", default_filename, "PDF Files (*.pdf)"
#             )
            
#             if not file_name:
#                 self.parent.statusBar.showMessage("Report generation cancelled.", 5000)
#                 return

#             # Initialize temporary directory
#             self._setup_temp_directory(file_name)
            
#             # Generate report sections
#             self._update_progress(10, "Generating metadata...")
#             metadata = self._generate_metadata()
            
#             self._update_progress(20, "Creating plots...")
#             plot_images = self._generate_plot_images_with_selection(selected_plots)
            
#             self._update_progress(60, "Creating tables...")
#             table_images = self._generate_table_images()
            
#             self._update_progress(80, "Assembling PDF...")
#             self._create_pdf_report(file_name, metadata, plot_images, table_images)
            
#             self._update_progress(95, "Cleaning up...")
#             self._cleanup_temp_files()
            
#             self._update_progress(100, "Complete!")
#             self.progress_dialog.close()
            
#             # Success message with detailed info
#             plot_count = len(plot_images)
#             custom_plot_count = len([p for p in plot_images if 'custom' in p[1].lower() or 'modified' in p[1].lower() or 'current' in p[1].lower()])
            
#             success_msg = f"""Comprehensive report successfully generated!

#                 Location: {file_name}
#                 Total Plots: {plot_count}
#                 Custom/Modified Plots: {custom_plot_count}
#                 Data Tables: {len(table_images)}
#                 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#                 The report includes your custom modifications and user-drawn plots."""
            
#             self.parent.statusBar.showMessage(f"Report successfully generated with {plot_count} plots", 5000)
#             QMessageBox.information(self.parent, "Success", success_msg)
            
#         except Exception as e:
#             if self.progress_dialog:
#                 self.progress_dialog.close()
#             self._cleanup_temp_files()
#             self.parent.handle_errors(f"Error generating report: {str(e)}\n{traceback.format_exc()}")
#             self.parent.statusBar.showMessage("Error generating report.", 5000)
    
#     def _generate_plot_images_with_selection(self, selected_plots):
#         """Generate plot images based on user selection."""
#         plot_images = []
        
#         # # Line 28: Debug parent type
#         # print(f"Parent type: {type(self.parent).__name__}")
        
#         # Add current plot if selected
#         if selected_plots.get('current_plot', False):
#             current_plot = self._capture_current_plot()
#             if current_plot:
#                 plot_images.append(current_plot)
        
#         # Add custom plots if selected
#         if selected_plots.get('custom_plots', False):
#             custom_plots = self._get_user_custom_plots()
#             plot_images.extend(custom_plots)
        
#         # Generate standard plots based on selection
#         plot_types = [
#             ("Wind Rose", "wind_rose"),
#             ("Wind Speed Distribution", "wind_speed_distribution"),
#             ("Turbulence Intensity", "turbulence_intensity"),
#             ("Wind Frequency Histogram", "wind_frequency_histogram"),
#             ("Power Curve", "power_curve"),
#             ("Actual Power Curve", "actual_power_curve"),
#             ("Binned Power Curve", "binned_power_curve"),
#             ("Rotor Speed Analysis", "rotor_speed_graph"),
#             ("Rotor Speed vs Gearbox Temperature", "rotor_speed_vs_gearbox_temperature"),
#             ("Ambient vs Nacelle Temperature", "ambient_vs_nacelle_temperature"),
#             ("Rotor Speed vs Generator Speed", "rotor_speed_vs_generator_speed"),
#             ("Joint Distribution", "joint_distribution")
#         ]
        
#         original_figure = self.parent.figure
#         original_plot = self.parent.selected_plot
        
#         for i, (plot_name, plot_type) in enumerate(plot_types):
#             if not selected_plots.get(plot_type, False):
#                 continue
                
#             try:
#                 progress = 20 + (i / len(plot_types)) * 40
#                 self._update_progress(int(progress), f"Creating {plot_name}...")
                
#                 cached_plot = self._get_cached_user_plot(plot_type)
#                 if cached_plot:
#                     plot_images.append(cached_plot)
#                     continue
                
#                 self.parent.selected_plot = plot_type
#                 self.parent.filtered_df = self.parent.get_filtered_data()
                
#                 if self.parent.filtered_df.empty:
#                     plot_images.append(self._create_error_plot(plot_name, "No data available"))
#                     continue
                
#                 # # Line 79: Debug data details
#                 # print(f"Plot type: {plot_type}")
#                 # print(f"Filtered data columns: {self.parent.filtered_df.columns.tolist()}")
#                 # print(f"Column cache: {getattr(self.parent, 'column_cache', 'Not available')}")
                
#                 new_fig = Figure(figsize=(10, 7))
#                 self.parent.figure = new_fig
                
#                 # Line 87: Use direct plot_selected_graph import
#                 plot_functions = {
#                     plot_type: lambda vw: plot_selected_graph(vw, plot_type, vw.column_cache)
#                 }
#                 plot_functions[plot_type](self.parent)
                
#                 self._enhance_plot_appearance(new_fig)
                
#                 image_path = os.path.join(self.temp_dir, f"{plot_type}.png")
#                 new_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                 plt.close(new_fig)
                
#                 plot_images.append((plot_name, image_path, self._get_plot_description(plot_type)))
                
#             except Exception as e:
#                 # Line 101: Enhanced error logging
#                 error_msg = f"Error generating plot {plot_type}: {str(e)}\n{traceback.format_exc()}"
#                 print(error_msg)
#                 plot_images.append(self._create_error_plot(plot_name, error_msg))
        
#         self.parent.figure = original_figure
#         self.parent.selected_plot = original_plot
#         self.parent.update_plot_signal.emit()
        
#         return plot_images

#     def _cleanup_temp_files(self):
#         """Clean up temporary files and directory."""
#         if self.temp_dir and os.path.exists(self.temp_dir):
#             try:
#                 import shutil
#                 shutil.rmtree(self.temp_dir)
#             except:
#                 pass
    
#     def _update_progress(self, value, message):
#         """Update progress dialog."""
#         if self.progress_dialog:
#             self.progress_dialog.setValue(value)
#             self.progress_dialog.setLabelText(message)
#             if self.progress_dialog.wasCanceled():
#                 raise Exception("Report generation cancelled by user")
    
#     def _setup_temp_directory(self, file_name):
#         """Setup temporary directory for images."""
#         self.temp_dir = os.path.join(os.path.dirname(file_name), f"temp_report_{datetime.now().strftime('%H%M%S')}")
#         os.makedirs(self.temp_dir, exist_ok=True)
    
#     def _generate_metadata(self):
#         """Generate comprehensive metadata for the report."""
#         data = self.parent.data
#         # turbine_id = self.turbine_id if self.turbine_id else getattr(self.parent, 'turbine_id', 'Unknown')    
#         turbine_id = getattr(self.parent, 'turbine_name', None) or (getattr(self.parent, 'windowTitle', lambda: 'Unknown')().split(': ')[-1] if ': ' in getattr(self.parent, 'windowTitle', lambda: 'Unknown')() else 'Unknown')
#         total_records = len(data)
#         date_range = None
#         if 'timestamp' in data.columns:
#             date_range = f"{data['timestamp'].min()} to {data['timestamp'].max()}"
        
#         missing_data = data.isnull().sum().sum()
#         data_completeness = ((total_records * len(data.columns) - missing_data) / 
#                         (total_records * len(data.columns)) * 100)
        
#         wind_stats = {}
#         if 'wind_speed' in data.columns:
#             wind_data = data['wind_speed'].dropna()
#             wind_stats = {
#                 'mean_wind_speed': wind_data.mean(),
#                 'max_wind_speed': wind_data.max(),
#                 'min_wind_speed': wind_data.min(),
#                 'wind_speed_std': wind_data.std(),
#                 'wind_speed_95th': wind_data.quantile(0.95),
#                 'wind_speed_median': wind_data.median()
#             }
        
#         power_stats = {}
#         if 'power' in data.columns:
#             power_data = data['power'].dropna()
#             if len(power_data) > 0:
#                 max_power = power_data.max()
#                 power_stats = {
#                     'mean_power': power_data.mean(),
#                     'max_power': max_power,
#                     'total_energy': power_data.sum() / (1000 * 24) if len(power_data) > 24 else power_data.sum() / 1000,
#                     'capacity_factor': (power_data.mean() / max_power * 100) if max_power > 0 else 0,
#                     'power_std': power_data.std(),
#                     'operational_hours': len(power_data[power_data > 0])
#                 }
        
#         return {
#             'turbine_id': turbine_id,
#             'data_period': date_range,
#             'total_records': total_records,
#             'data_completeness': data_completeness,
#             'missing_data_points': missing_data,
#             'wind_statistics': wind_stats,
#             'power_statistics': power_stats,
#             'columns': list(data.columns),
#         }
        
#     def _generate_plot_images(self):
#         """Generate plot images for all available plot types."""
#         plot_images = []
        
#         # Line 116: Debug parent type
#         print(f"Parent type: {type(self.parent).__name__}")
        
#         plot_types = [
#             ("Wind Rose", "wind_rose"),
#             ("Wind Speed Distribution", "wind_speed_distribution"),
#             ("Turbulence Intensity", "turbulence_intensity"),
#             ("Wind Frequency Histogram", "wind_frequency_histogram"),
#             ("Power Curve", "power_curve"),
#             ("Actual Power Curve", "actual_power_curve"),
#             ("Binned Power Curve", "binned_power_curve"),
#             ("Rotor Speed Analysis", "rotor_speed_graph"),
#             ("Power vs Generator Temperature", "power_vs_generator_temperature"),
#             ("Rotor Speed vs Gearbox Temperature", "rotor_speed_vs_gearbox_temperature"),
#             ("Ambient vs Nacelle Temperature", "ambient_vs_nacelle_temperature"),
#             ("Rotor Speed vs Generator Speed", "rotor_speed_vs_generator_speed"),
#             ("Joint Distribution", "joint_distribution")
#         ]
        
#         original_figure = self.parent.figure
#         original_plot = self.parent.selected_plot
        
#         for i, (plot_name, plot_type) in enumerate(plot_types):
#             try:
#                 progress = 20 + (i / len(plot_types)) * 40
#                 self._update_progress(int(progress), f"Creating {plot_name}...")
                
#                 self.parent.selected_plot = plot_type
#                 self.parent.filtered_df = self.parent.get_filtered_data()
                
#                 if self.parent.filtered_df.empty:
#                     plot_images.append(self._create_error_plot(plot_name, "No data available"))
#                     continue
                
#                 # Line 150: Debug data details
#                 print(f"Plot type: {plot_type}")
#                 print(f"Filtered data columns: {self.parent.filtered_df.columns.tolist()}")
#                 print(f"Column cache: {getattr(self.parent, 'column_cache', 'Not available')}")
                
#                 new_fig = Figure(figsize=(10, 7))
#                 self.parent.figure = new_fig
                
#                 # Line 158: Use direct plot_selected_graph import
#                 plot_functions = {
#                     plot_type: lambda vw: plot_selected_graph(vw, plot_type, vw.column_cache)
#                 }
#                 plot_functions[plot_type](self.parent)
                
#                 self._enhance_plot_appearance(new_fig)
                
#                 image_path = os.path.join(self.temp_dir, f"{plot_type}.png")
#                 new_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                 plt.close(new_fig)
                
#                 plot_images.append((plot_name, image_path, self._get_plot_description(plot_type)))
                
#             except Exception as e:
#                 # Line 172: Enhanced error logging
#                 error_msg = f"Error generating plot {plot_type}: {str(e)}\n{traceback.format_exc()}"
#                 print(error_msg)
#                 plot_images.append(self._create_error_plot(plot_name, error_msg))
        
#         self.parent.figure = original_figure
#         self.parent.selected_plot = original_plot
#         self.parent.update_plot_signal.emit()
        
#         return plot_images
    
#     def _enhance_plot_appearance(self, fig):
#         """Enhance plot appearance with professional styling."""
#         fig.patch.set_facecolor('white')
#         fig.patch.set_edgecolor('black')
#         fig.patch.set_linewidth(1.5)
        
#         for ax in fig.axes:
#             ax.set_facecolor('white')
            
#             # Professional grid styling
#             ax.grid(True, color='#D0D0D0', linestyle='-', linewidth=0.6, alpha=0.7, zorder=0)
#             ax.set_axisbelow(True)
            
#             # Enhanced frame styling - show all spines with professional appearance
#             for spine_name in ax.spines:
#                 ax.spines[spine_name].set_visible(True)
#                 ax.spines[spine_name].set_color('#333333')
#                 ax.spines[spine_name].set_linewidth(1.2)
            
#             # Professional tick styling
#             ax.tick_params(colors='#2E2E2E', labelsize=11, direction='out', 
#                         length=5, width=1.1, pad=4)
#             ax.tick_params(which='minor', colors='#2E2E2E', direction='out', 
#                         length=3, width=0.8)
            
#             # Enhanced axis labels
#             if hasattr(ax, 'xaxis') and hasattr(ax.xaxis, 'label'):
#                 ax.xaxis.label.set_color('#1A1A1A')
#                 ax.xaxis.label.set_fontsize(13)
#                 ax.xaxis.label.set_fontweight('bold')
#                 ax.xaxis.label.set_fontfamily('serif')
            
#             if hasattr(ax, 'yaxis') and hasattr(ax.yaxis, 'label'):
#                 ax.yaxis.label.set_color('#1A1A1A')
#                 ax.yaxis.label.set_fontsize(13)
#                 ax.yaxis.label.set_fontweight('bold')
#                 ax.yaxis.label.set_fontfamily('serif')
            
#             # Professional title styling
#             if hasattr(ax, 'title') and ax.title.get_text():
#                 ax.title.set_color('#0D47A1')
#                 ax.title.set_fontsize(16)
#                 ax.title.set_fontweight('bold')
#                 ax.title.set_fontfamily('serif')
#                 ax.set_title(ax.get_title(), pad=20)
            
#             # Enhanced legend styling
#             legend = ax.get_legend()
#             if legend:
#                 legend.get_frame().set_facecolor('#F8F9FA')
#                 legend.get_frame().set_edgecolor('#333333')
#                 legend.get_frame().set_linewidth(1.0)
#                 legend.get_frame().set_alpha(0.95)
#                 legend.get_frame().set_boxstyle("round,pad=0.5")
#                 legend.set_title(legend.get_title().get_text(), prop={'weight': 'bold', 'size': 11})
#                 for text in legend.get_texts():
#                     text.set_color('#1A1A1A')
#                     text.set_fontsize(11)
#                     text.set_fontfamily('serif')
            
#             # Add professional plot margins
#             ax.margins(x=0.02, y=0.02)
        
#         # Ensure tight layout with proper spacing
#         fig.tight_layout(pad=2.0)

#     def _create_error_plot(self, plot_name, error_msg):
#         """Create placeholder plot for errors."""
#         fig = Figure(figsize=(10, 7))
#         ax = fig.add_subplot(111)
#         ax.text(0.5, 0.5, f"Plot Not Available\n\n{plot_name}\n\nReason: {error_msg}", 
#                 ha='center', va='center', fontsize=12, color='red',
#                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
#         ax.set_xlim(0, 1)
#         ax.set_ylim(0, 1)
#         ax.set_axis_off()
        
#         image_path = os.path.join(self.temp_dir, f"error_{plot_name.replace(' ', '_')}.png")
#         fig.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
#         plt.close(fig)
        
#         return (plot_name, image_path, "Plot could not be generated due to data issues.")
    
#     def _get_plot_description(self, plot_type):
#         """Get description for each plot type."""
#         descriptions = {
#             'wind_rose': "Wind rose diagram showing wind direction frequency and speed distribution.",
#             'wind_speed_distribution': "Statistical distribution of wind speeds over the analysis period.",
#             'turbulence_intensity': "Turbulence intensity analysis showing wind variability characteristics.",
#             'power_curve': "Theoretical power curve showing expected power output vs wind speed.",
#             'actual_power_curve': "Actual measured power curve compared to theoretical values.",
#             'binned_power_curve': "Binned power curve analysis for performance assessment.",
#             'rotor_speed_graph': "Rotor speed variations and operational characteristics.",
#             'rotor_speed_vs_gearbox_temperature': "Relationship between rotor speed and gearbox thermal behavior.",
#             'ambient_vs_nacelle_temperature': "Temperature differential analysis between ambient and nacelle.",
#             'rotor_speed_vs_generator_speed': "Gearbox ratio analysis and mechanical efficiency.",
#             'joint_distribution': "Multi-variable distribution analysis of key parameters."
#         }
#         return descriptions.get(plot_type, "Analysis of turbine operational parameters.")
    
#     def _generate_table_images(self):
#         """Generate table images with enhanced formatting."""
#         tables = [
#             ("Executive Summary", self.parent.summary_table),
#             ("Statistical Analysis", self.parent.stats_table),
#             ("Bin Analysis Records", getattr(self.parent, 'bin_table', None)),
#             ("Performance Bands", getattr(self.parent, 'percentage_bands_table', None) 
#              if getattr(self.parent, 'enable_percentage_bands', False) and 
#              hasattr(self.parent, 'enable_percentage_bands') and 
#              self.parent.enable_percentage_bands.isChecked() else None),
#             ("Standard Power Data", self.parent.standard_data_table),
#             ("Filtered Data Records", getattr(self.parent, 'removed_data_table', None)
#              if getattr(self.parent, 'remove_negative_power', False) and 
#              hasattr(self.parent, 'remove_negative_power') and 
#              self.parent.remove_negative_power.isChecked() else None)
#         ]
        
#         table_images = []
#         for table_name, table in tables:
#             if table is None:
#                 continue
                
#             try:
#                 # Create enhanced table image
#                 fig, ax = plt.subplots(figsize=(12, 8))
#                 ax.axis('off')
                
#                 # Extract table data
#                 data = []
#                 headers = []
                
#                 # Get headers
#                 for col in range(table.columnCount()):
#                     header_item = table.horizontalHeaderItem(col)
#                     headers.append(header_item.text() if header_item else f"Col {col}")
                
#                 # Get data
#                 for row in range(min(table.rowCount(), 50)):  # Limit rows for readability
#                     row_data = []
#                     for col in range(table.columnCount()):
#                         item = table.item(row, col)
#                         row_data.append(item.text() if item else "")
#                     data.append(row_data)
                
#                 if data:  # Only create table if there's data
#                     # Create table
#                     table_plot = ax.table(cellText=data, colLabels=headers, 
#                                         loc='center', cellLoc='center')
                    
#                     # Style the table
#                     table_plot.auto_set_font_size(False)
#                     table_plot.set_fontsize(8)
#                     table_plot.scale(1, 2)
                    
#                     # Style headers
#                     for i in range(len(headers)):
#                         table_plot[(0, i)].set_facecolor('#4472C4')
#                         table_plot[(0, i)].set_text_props(weight='bold', color='white')
                    
#                     # Alternate row colors
#                     for i in range(1, len(data) + 1):
#                         for j in range(len(headers)):
#                             if i % 2 == 0:
#                                 table_plot[(i, j)].set_facecolor('#F2F2F2')
#                             else:
#                                 table_plot[(i, j)].set_facecolor('white')
                
#                 # Add title
#                 plt.title(table_name, fontsize=14, fontweight='bold', pad=20)
                
#                 # Save table image
#                 image_path = os.path.join(self.temp_dir, f"{table_name.replace(' ', '_')}.png")
#                 fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                 plt.close(fig)
                
#                 table_images.append((table_name, image_path))
                
#             except Exception as e:
#                 print(f"Error generating table {table_name}: {e}")
#                 continue
        
#         return table_images
    
#     def _create_pdf_report(self, file_name, metadata, plot_images, table_images):
#         """Create comprehensive PDF report with enhanced professional layout."""
#         doc = SimpleDocTemplate(file_name, pagesize=A4, 
#                             leftMargin=2*cm, rightMargin=2*cm,
#                             topMargin=2.5*cm, bottomMargin=2*cm)
#         elements = []
#         styles = getSampleStyleSheet()       
#         title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
#                                 fontSize=26, spaceAfter=30, alignment=TA_CENTER,
#                                 textColor=colors.HexColor('#1565C0'), fontName='Helvetica-Bold')
        
#         heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
#                                     fontSize=16, spaceAfter=18, spaceBefore=24,
#                                     textColor=colors.HexColor('#1976D2'), fontName='Helvetica-Bold')
#         subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'],
#                                         fontSize=14, spaceAfter=12, spaceBefore=16,
#                                         textColor=colors.HexColor('#424242'), fontName='Helvetica-Bold')
#         normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
#                                     fontSize=11, spaceAfter=12, alignment=TA_LEFT,
#                                     fontName='Helvetica', leading=14)
#         caption_style = ParagraphStyle('Caption', parent=styles['Normal'],
#                                     fontSize=9, spaceAfter=8, alignment=TA_CENTER,
#                                     textColor=colors.HexColor('#666666'),
#                                     fontName='Helvetica-Oblique')
        
#         elements.extend(self._create_title_page(metadata, title_style, heading_style, normal_style))
#         elements.append(PageBreak())
#         elements.extend(self._create_table_of_contents(plot_images, table_images, heading_style, normal_style))
#         elements.append(PageBreak())
#         elements.extend(self._create_executive_summary(metadata, heading_style, normal_style))
#         elements.append(PageBreak())
#         elements.append(Paragraph("Performance Analysis & Visualizations", heading_style))
#         elements.append(Spacer(1, 0.3*inch))
        
#         for i, (plot_name, image_path, description) in enumerate(plot_images):
#             elements.append(KeepTogether([
#                 Paragraph(f"{i+1}. {plot_name}", subheading_style),
#                 Spacer(1, 0.15*inch),
#                 Image(image_path, width=7*inch, height=4.9*inch),
#                 Spacer(1, 0.1*inch),
#                 Paragraph(f"Figure {i+1}: {description}", caption_style),
#                 Spacer(1, 0.25*inch)
#             ]))
            
#             if (i + 1) % 2 == 0 and i < len(plot_images) - 1:
#                 elements.append(PageBreak())
        
#         if table_images:
#             elements.append(PageBreak())
#             elements.append(Paragraph("Statistical Data Tables", heading_style))
#             elements.append(Spacer(1, 0.3*inch))
            
#             for i, (table_name, image_path) in enumerate(table_images):
#                 elements.append(KeepTogether([
#                     Paragraph(f"{i+1}. {table_name}", subheading_style),
#                     Spacer(1, 0.15*inch),
#                     Image(image_path, width=7.5*inch, height=5*inch),
#                     Spacer(1, 0.25*inch)
#                 ]))
        
#         elements.append(PageBreak())
#         elements.extend(self._create_report_footer(metadata, normal_style))
        
#         doc.build(elements)
    
#     # def _create_title_page(self, metadata, title_style, heading_style, normal_style):
#     #     """Create professional title page."""
#     #     elements = []
        
#     #     project_title = getattr(self.parent, 'project_title', None)
#     #     if not project_title:
#     #         project_title = getattr(self.parent, 'project_file_name', 'Wind Turbine Performance Analysis')
    
#     #     turbine_id = metadata.get('turbine_id', 'Unknown')
#     #     elements.append(Spacer(1, 1.5*inch))
#     #     elements.append(Paragraph(f"{project_title}", title_style))
#     #     elements.append(Spacer(1, 0.3*inch))
#     #     elements.append(Paragraph(f"Turbine ID: {turbine_id}", heading_style))
#     #     elements.append(Spacer(1, 0.5*inch))
        
#     #     report_data = [
#     #         ['Analysis Period:', metadata.get('data_period', 'Full Dataset')],
#     #         ['Total Data Points:', f"{metadata['total_records']:,}"],
#     #         ['Data Quality:', f"{metadata['data_completeness']:.1f}% Complete"],
#     #         ['Analyzed Parameters:', f"{len(metadata['columns'])} Columns"]
#     #     ]
        
#     #     report_table = Table(report_data, colWidths=[2.2*inch, 3.3*inch])
#     #     report_table.setStyle(TableStyle([
#     #         ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1565C0')),
#     #         ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8F9FA')),
#     #         ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
#     #         ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
#     #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#     #         ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#     #         ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
#     #         ('FONTSIZE', (0, 0), (-1, -1), 11),
#     #         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
#     #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     #         ('LEFTPADDING', (0, 0), (-1, -1), 8),
#     #         ('RIGHTPADDING', (0, 0), (-1, -1), 8),
#     #         ('TOPPADDING', (0, 0), (-1, -1), 6),
#     #         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#     #     ]))
        
#     #     elements.append(report_table)
#     #     elements.append(Spacer(1, 0.8*inch))
        
#     #     if metadata['wind_statistics']:
#     #         ws = metadata['wind_statistics']
#     #         elements.append(Paragraph("Wind Characteristics Summary", heading_style))
#     #         wind_summary_data = [
#     #             ['Mean Wind Speed:', f"{ws.get('mean_wind_speed', 0):.2f} m/s"],
#     #             ['Maximum Wind Speed:', f"{ws.get('max_wind_speed', 0):.2f} m/s"],
#     #             ['95th Percentile:', f"{ws.get('wind_speed_95th', 0):.2f} m/s"],
#     #             ['Standard Deviation:', f"{ws.get('wind_speed_std', 0):.2f} m/s"]
#     #         ]
#     #         wind_table = Table(wind_summary_data, colWidths=[2.2*inch, 3.3*inch])
#     #         wind_table.setStyle(TableStyle([
#     #             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#388E3C')),
#     #             ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F1F8E9')),
#     #             ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
#     #             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#     #             ('FONTSIZE', (0, 0), (-1, -1), 10),
#     #             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
#     #             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     #             ('LEFTPADDING', (0, 0), (-1, -1), 8),
#     #             ('RIGHTPADDING', (0, 0), (-1, -1), 8),
#     #         ]))
#     #         elements.append(wind_table)
#     #         elements.append(Spacer(1, 0.3*inch))
        
#     #     if metadata['power_statistics']:
#     #         ps = metadata['power_statistics']
#     #         elements.append(Paragraph("Power Performance Summary", heading_style))
#     #         power_summary_data = [
#     #             ['Average Power Output:', f"{ps.get('mean_power', 0):.2f} kW"],
#     #             ['Maximum Power Output:', f"{ps.get('max_power', 0):.2f} kW"],
#     #             ['Estimated Energy Production:', f"{ps.get('total_energy', 0):.2f} MWh"],
#     #             ['Capacity Factor:', f"{ps.get('capacity_factor', 0):.1f}%"],
#     #             ['Operational Hours:', f"{ps.get('operational_hours', 0):,}"]
#     #         ]
#     #         power_table = Table(power_summary_data, colWidths=[2.2*inch, 3.3*inch])
#     #         power_table.setStyle(TableStyle([
#     #             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F57C00')),
#     #             ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FFF8E1')),
#     #             ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
#     #             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#     #             ('FONTSIZE', (0, 0), (-1, -1), 10),
#     #             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
#     #             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     #             ('LEFTPADDING', (0, 0), (-1, -1), 8),
#     #             ('RIGHTPADDING', (0, 0), (-1, -1), 8),
#     #         ]))
#     #         elements.append(power_table)
        
#     #     return elements
    
#     def _create_title_page(self, metadata, title_style, heading_style, normal_style):
#         """Create professional title page."""
#         elements = []
        
#         # Get project info from database
#         project_info = self._get_project_info()
        
#         project_title = project_info.get('name', 'Wind Turbine Performance Analysis')
#         turbine_id = metadata.get('turbine_id', 'Unknown')
        
#         elements.append(Spacer(1, 1.5*inch))
#         elements.append(Paragraph(f"{project_title}", title_style))
#         elements.append(Spacer(1, 0.3*inch))
#         elements.append(Paragraph(f"Turbine ID: {turbine_id}", heading_style))
#         elements.append(Spacer(1, 0.5*inch))
        
#         report_data = [
#             ['Project Name:', project_info.get('name', 'N/A')],
#             ['Company:', project_info.get('company', 'N/A')],
#             ['Location:', project_info.get('location', 'N/A')],
#             ['Capacity:', project_info.get('capacity', 'N/A')],
#             ['Model:', project_info.get('model_name', 'N/A')],
#             ['Analysis Period:', metadata.get('data_period', 'Full Dataset')],
#             ['Total Data Points:', f"{metadata['total_records']:,}"],
#             ['Data Quality:', f"{metadata['data_completeness']:.1f}% Complete"]
#         ]
        
#         report_table = Table(report_data, colWidths=[2.2*inch, 3.3*inch])
#         report_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1565C0')),
#             ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8F9FA')),
#             ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
#             ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#             ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
#             ('FONTSIZE', (0, 0), (-1, -1), 11),
#             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('LEFTPADDING', (0, 0), (-1, -1), 8),
#             ('RIGHTPADDING', (0, 0), (-1, -1), 8),
#             ('TOPPADDING', (0, 0), (-1, -1), 6),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#         ]))
        
#         elements.append(report_table)
#         elements.append(Spacer(1, 0.8*inch))
#         return elements
    
#     def _create_table_of_contents(self, plot_images, table_images, heading_style, normal_style):
#         """Create table of contents."""
#         elements = []
#         elements.append(Paragraph("Table of Contents", heading_style))
#         elements.append(Spacer(1, 0.3*inch))
        
#         toc_data = [
#             ['Section', 'Page'],
#             ['Executive Summary', '3'],
#             ['Data Analysis & Visualizations', '4']
#         ]
        
#         # page_num = 5
#         # for plot_name, _, _ in plot_images[:5]:  # Show first 5 plots
#         #     toc_data.append([f"  • {plot_name}", str(page_num)])
#         #     page_num += 1
        
#         # if len(plot_images) > 5:
#         #     toc_data.append([f"  • ... and {len(plot_images)-5} more plots", "..."])
        
#         page_num = 5
#         for plot_name, _, _ in plot_images:  # Show ALL plots
#             toc_data.append([f"  • {plot_name}", str(page_num)])
#             page_num += 1

#         if table_images:
#             toc_data.append(['Data Tables & Statistics', str(page_num)])
        
#         toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
#         toc_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, -1), 11),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ]))
        
#         elements.append(toc_table)
#         return elements
    
#     def _create_executive_summary(self, metadata, heading_style, normal_style):
#         """Create comprehensive executive summary section."""
#         elements = []
#         elements.append(Paragraph("Executive Summary", heading_style))
#         elements.append(Spacer(1, 0.2*inch))
        
#         summary_text = f"""
#         This comprehensive performance analysis report provides detailed insights into the operational 
#         characteristics of Wind Turbine {metadata['turbine_id']} based on {metadata['total_records']:,} 
#         data records collected over {metadata.get('data_period', 'the analysis period')}. The dataset 
#         demonstrates {metadata['data_completeness']:.1f}% completeness, ensuring reliable statistical analysis.
#         """
        
#         elements.append(Paragraph(summary_text, normal_style))
#         elements.append(Spacer(1, 0.2*inch))
        
#         key_findings = []
        
#         if metadata['wind_statistics']:
#             ws = metadata['wind_statistics']
#             wind_finding = f"""
#             <b>Wind Resource Assessment:</b> The site experienced an average wind speed of 
#             {ws.get('mean_wind_speed', 0):.2f} m/s with maximum recorded speeds reaching 
#             {ws.get('max_wind_speed', 0):.2f} m/s. Wind variability, measured by standard deviation 
#             ({ws.get('wind_speed_std', 0):.2f} m/s), indicates {'moderate' if ws.get('wind_speed_std', 0) < 3 else 'high'} 
#             turbulence characteristics typical for this wind regime.
#             """
#             key_findings.append(wind_finding)
        
#         if metadata['power_statistics']:
#             ps = metadata['power_statistics']
#             cf = ps.get('capacity_factor', 0)
#             cf_rating = 'excellent' if cf > 40 else 'good' if cf > 30 else 'moderate' if cf > 20 else 'low'
            
#             power_finding = f"""
#             <b>Power Performance:</b> The turbine achieved an average power output of 
#             {ps.get('mean_power', 0):.2f} kW with a capacity factor of {cf:.1f}%, indicating 
#             {cf_rating} performance relative to industry standards. Total estimated energy 
#             production reached {ps.get('total_energy', 0):.2f} MWh during the analysis period.
#             """
#             key_findings.append(power_finding)
        
#         data_quality_finding = f"""
#         <b>Data Quality Assessment:</b> The analysis is based on high-quality data with 
#         {metadata['data_completeness']:.1f}% completeness. Missing data points 
#         ({metadata['missing_data_points']:,} out of {metadata['total_records'] * len(metadata['columns']):,}) 
#         have been appropriately handled to ensure statistical validity.
#         """
#         key_findings.append(data_quality_finding)
        
#         for finding in key_findings:
#             elements.append(Paragraph(finding, normal_style))
#             elements.append(Spacer(1, 0.15*inch))
        
#         recommendations = """
#         <b>Report Structure:</b> This report presents comprehensive visualizations including wind 
#         resource analysis, power performance curves, temperature correlations, and operational 
#         parameter relationships. Each visualization is accompanied by detailed descriptions and 
#         statistical interpretations to support engineering decision-making and performance optimization.
#         """
        
#         elements.append(Paragraph(recommendations, normal_style))
#         return elements
    
#     def _create_report_footer(self, metadata, normal_style):
#         """Create report footer with additional information."""
#         elements = []
        
#         footer_text = f"""
#         <b>Report Information</b><br/>
#         Data columns analyzed: {len(metadata['columns'])}<br/>
#         Total data points: {metadata['total_records']:,}<br/>
#         Missing data points: {metadata['missing_data_points']:,}<br/>
        
#         <b>Disclaimer</b><br/>
#         This report is generated based on the provided data and should be used in conjunction with 
#         engineering judgment and site-specific knowledge. All measurements and calculations are 
#         subject to instrumentation accuracy and data quality limitations.
#         """
        
#         elements.append(Paragraph(footer_text, normal_style))
#         return elements
    
#     def _capture_current_plot(self):
#         """Capture the currently displayed plot if it's user-modified."""
#         try:
#             if self.parent.figure and hasattr(self.parent.figure, 'axes') and self.parent.figure.axes:
#                 # Check if the current plot has been modified by looking for custom elements
#                 current_plot_type = getattr(self.parent, 'selected_plot', 'current_plot')
                
#                 # Create a copy of the current figure
#                 current_fig = self.parent.figure
                
#                 # Save the current plot
#                 image_path = os.path.join(self.temp_dir, f"current_user_plot_{current_plot_type}.png")
#                 current_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                
#                 plot_name = f"Current Plot ({current_plot_type.replace('_', ' ').title()})"
#                 description = "User's currently displayed plot with any modifications applied."
                
#                 return (plot_name, image_path, description)
#         except Exception as e:
#             print(f"Error capturing current plot: {e}")
#         return None
    
#     def _get_user_custom_plots(self):
#         """Get user-saved custom plots from various sources."""
#         custom_plots = []
        
#         try:
#             # Check if parent has a custom plots storage
#             if hasattr(self.parent, 'custom_plots') and self.parent.custom_plots:
#                 for plot_name, plot_data in self.parent.custom_plots.items():
#                     if isinstance(plot_data, dict) and 'figure' in plot_data:
#                         image_path = os.path.join(self.temp_dir, f"custom_{plot_name.replace(' ', '_')}.png")
#                         plot_data['figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                         description = plot_data.get('description', 'User-created custom plot')
#                         custom_plots.append((plot_name, image_path, description))
            
#             # Check for matplotlib figures stored in parent
#             if hasattr(self.parent, 'saved_figures') and self.parent.saved_figures:
#                 for i, (fig, metadata) in enumerate(self.parent.saved_figures):
#                     plot_name = metadata.get('name', f'Custom Plot {i+1}')
#                     image_path = os.path.join(self.temp_dir, f"saved_figure_{i}.png")
#                     fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                     description = metadata.get('description', 'User-saved custom figure')
#                     custom_plots.append((plot_name, image_path, description))
            
#             # Check for plot modifications cache
#             if hasattr(self.parent, 'plot_modifications') and self.parent.plot_modifications:
#                 for plot_type, modifications in self.parent.plot_modifications.items():
#                     if 'modified_figure' in modifications:
#                         plot_name = f"Modified {plot_type.replace('_', ' ').title()}"
#                         image_path = os.path.join(self.temp_dir, f"modified_{plot_type}.png")
#                         modifications['modified_figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                         description = f"User-modified version of {plot_type} with custom adjustments"
#                         custom_plots.append((plot_name, image_path, description))
                        
#         except Exception as e:
#             print(f"Error getting user custom plots: {e}")
        
#         return custom_plots
    
#     def _get_cached_user_plot(self, plot_type):
#         """Get cached user-modified version of a specific plot type."""
#         try:
#             # Check if user has cached modifications for this plot type
#             if hasattr(self.parent, 'plot_cache') and plot_type in self.parent.plot_cache:
#                 cached_data = self.parent.plot_cache[plot_type]
                
#                 if 'figure' in cached_data:
#                     plot_name = cached_data.get('name', plot_type.replace('_', ' ').title())
#                     image_path = os.path.join(self.temp_dir, f"cached_{plot_type}.png")
#                     cached_data['figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                     description = cached_data.get('description', f'Cached user version of {plot_type}')
#                     return (plot_name, image_path, description)
            
#             # Check if there's a user-modified canvas for this plot type
#             if hasattr(self.parent, 'canvas') and hasattr(self.parent.canvas, 'figure'):
#                 # Check if current canvas figure matches the plot type we're looking for
#                 current_selected = getattr(self.parent, 'selected_plot', None)
#                 if current_selected == plot_type:
#                     # Check if the figure has been modified (has custom annotations, etc.)
#                     fig = self.parent.canvas.figure
#                     if self._is_figure_modified(fig):
#                         plot_name = f"Modified {plot_type.replace('_', ' ').title()}"
#                         image_path = os.path.join(self.temp_dir, f"user_modified_{plot_type}.png")
#                         fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
#                         description = f'User-modified {plot_type} with custom elements'
#                         return (plot_name, image_path, description)
                        
#         except Exception as e:
#             print(f"Error getting cached user plot for {plot_type}: {e}")
        
#         return None
    
#     def _is_figure_modified(self, fig):
#         """Check if a figure has been modified by the user."""
#         try:
#             # Check for custom annotations, text, or additional elements
#             for ax in fig.axes:
#                 # Check for user-added text annotations
#                 if hasattr(ax, 'texts') and len(ax.texts) > 0:
#                     for text in ax.texts:
#                         # Check if text is not a default axis label
#                         if text.get_text() and not any(label in text.get_text().lower() 
#                                                      for label in ['xlabel', 'ylabel', 'title']):
#                             return True
                
#                 # Check for user-added lines or patches
#                 if hasattr(ax, 'lines') and len(ax.lines) > 1:  # More than just data lines
#                     return True
#                 # Check for custom patches (shapes, rectangles, etc.)
#                 if hasattr(ax, 'patches') and len(ax.patches) > 0:
#                     return True
#                 # Check for custom collections (scatter plots, etc.)
#                 if hasattr(ax, 'collections') and len(ax.collections) > 1:
#                     return True
#             # Check for custom figure-level elements
#             if hasattr(fig, 'texts') and len(fig.texts) > 0:
#                 return True
#         except Exception as e:
#             print(f"Error checking if figure is modified: {e}")
#         return False
#     def _save_user_plot_for_future(self, plot_type, figure, description=""):
#         """Save user-modified plot for future use."""
#         try:
#             if not hasattr(self.parent, 'plot_cache'):
#                 self.parent.plot_cache = {}
            
#             self.parent.plot_cache[plot_type] = {
#                 'figure': figure,
#                 'description': description,
#                 'timestamp': datetime.now(),
#                 'name': plot_type.replace('_', ' ').title()
#             }
#         except Exception as e:
#             print(f"Error saving user plot: {e}")

#     def _create_plot_selection_dialog(self):
#         """Create modern dialog for plot selection with fixed checkmarks."""
        
#         dialog = QDialog(self.parent if hasattr(self, 'parent') else self)
#         dialog.setWindowTitle("Generate Report - Select Plots")
#         dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
#         # FIX 1: Increased width to 850 to prevents text cutoff
#         dialog.setFixedSize(850, 800)
        
#         # Base64 encoded white checkmark icon
#         check_icon = "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAADkSURBVDjLtZPBSgMxEEVt86ygBQ8e/EC96EVE8O/8AX/A0r/wY3wQDx78iSIqzMKC7IXiZmctM52Wwu6CJNm8d2cScB4W10c49i5+fF8h/xsC2u0Du38C+82y+6LVAw4Ab7OZR73/pP8D1EzjBqMctYtT2yJ3gIvn46Wz8zMHyCLdZPAyp6iW5e4AfrM9amFlVe/O0aXV1sB+s+y+ALWIVmmq5LvvFjQHz0cfrmyH3KPdGziE9xMQB2TV5O6F02d0EibXJ6ch4szl4sB6dSBv5uXCCFjIXyy7L1o94ADwNpt5/ALWN28zHQpFAAAAAElFTkSuQmCC)"

#         dialog.setStyleSheet(f"""
#             QDialog {{
#                 background-color: #2C3E50;
#             }}
#             QLabel#title {{
#                 font-size: 20px;
#                 font-weight: bold;
#                 color: #ECF0F1;
#                 padding: 20px 20px 10px 20px;
#             }}
#             QLabel#subtitle {{
#                 font-size: 13px;
#                 color: #BDC3C7;
#                 padding: 0px 20px 15px 20px;
#             }}
#             QLabel#sectionHeader {{
#                 font-size: 15px;
#                 font-weight: bold;
#                 color: #3498DB;
#                 padding: 15px 5px 5px 5px;
#                 border-bottom: 1px solid #34495E;
#             }}
            
#             /* CHECKBOX STYLING */
#             QCheckBox {{
#                 font-size: 14px;
#                 color: #ECF0F1;
#                 padding: 8px;
#                 spacing: 12px;
#                 min-width: 400px; /* FIX 2: Force width to prevent text cutoff */
#             }}
#             QCheckBox::indicator {{
#                 width: 22px;
#                 height: 22px;
#                 border: 2px solid #5D6D7E;
#                 border-radius: 4px;
#                 background: #34495E;
#             }}
#             QCheckBox::indicator:checked {{
#                 background-color: #3498DB;
#                 border-color: #3498DB;
#                 /* FIX 3: Added the Base64 image here */
#                 image: {check_icon};
#             }}
#             QCheckBox::indicator:hover {{
#                 border-color: #3498DB;
#             }}

#             /* BUTTON STYLING */
#             QPushButton {{
#                 background-color: #2980B9;
#                 color: white;
#                 border: none;
#                 padding: 10px 20px;
#                 font-size: 13px;
#                 font-weight: bold;
#                 border-radius: 6px;
#                 min-width: 100px;
#             }}
#             QPushButton:hover {{
#                 background-color: #3498DB;
#             }}
#             QPushButton#secondary {{
#                 background-color: transparent;
#                 border: 2px solid #2980B9;
#                 color: #3498DB;
#             }}
#             QPushButton#secondary:hover {{
#                 background-color: #2980B9;
#                 color: white;
#             }}
            
#             /* SCROLLBAR & FRAMES */
#             QScrollBar:vertical {{
#                 border: none;
#                 background: #2C3E50;
#                 width: 10px;
#                 margin: 0px;
#             }}
#             QScrollBar::handle:vertical {{
#                 background: #5D6D7E;
#                 min-height: 20px;
#                 border-radius: 5px;
#             }}
#             QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
#                 height: 0px;
#             }}
#             QFrame#separator {{
#                 background-color: #34495E;
#                 margin: 0px;
#             }}
#         """)
        
#         main_layout = QVBoxLayout()
#         main_layout.setSpacing(0)
#         main_layout.setContentsMargins(0, 0, 0, 0)
        
#         # --- Header ---
#         title = QLabel("Generate Comprehensive Report")
#         title.setObjectName("title")
#         main_layout.addWidget(title)
        
#         subtitle = QLabel("Select the plots and visualizations to include in your PDF report.")
#         subtitle.setObjectName("subtitle")
#         main_layout.addWidget(subtitle)
        
#         # Separator
#         sep = QFrame()
#         sep.setObjectName("separator")
#         sep.setFrameShape(QFrame.HLine)
#         sep.setFixedHeight(1)
#         main_layout.addWidget(sep)
        
#         # --- Scroll Area ---
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         scroll.setStyleSheet("background: transparent; border: none;") # Ensure transparency
        
#         scroll_widget = QWidget()
#         scroll_widget.setObjectName("scrollContent")
#         scroll_widget.setStyleSheet("background: transparent;") # Ensure transparency
        
#         scroll_layout = QVBoxLayout()
#         scroll_layout.setSpacing(5)
#         scroll_layout.setContentsMargins(30, 10, 30, 10)
        
#         checkboxes = {}
        
#         # 1. Custom Plots Section
#         special_section = QLabel("Current & Custom Plots")
#         special_section.setObjectName("sectionHeader")
#         scroll_layout.addWidget(special_section)
        
#         current_cb = QCheckBox("Current Displayed Plot (with modifications)")
#         current_cb.setChecked(True)
#         scroll_layout.addWidget(current_cb)
#         checkboxes['current_plot'] = current_cb
        
#         parent_obj = self.parent if hasattr(self, 'parent') else self
#         if hasattr(parent_obj, 'custom_plots') or hasattr(parent_obj, 'saved_figures'):
#             custom_cb = QCheckBox("All Custom/Saved Plots")
#             custom_cb.setChecked(True)
#             scroll_layout.addWidget(custom_cb)
#             checkboxes['custom_plots'] = custom_cb
        
#         # 2. Standard Plots Section
#         scroll_layout.addSpacing(15)
#         standard_section = QLabel("Standard Analysis Plots")
#         standard_section.setObjectName("sectionHeader")
#         scroll_layout.addWidget(standard_section)
        
#         plot_types = [
#             ("Wind Rose", "wind_rose"),
#             ("Wind Speed Distribution", "wind_speed_distribution"),
#             ("Turbulence Intensity", "turbulence_intensity"),
#             ("Wind Frequency Histogram", "wind_frequency_histogram"),
#             ("Power Curve", "power_curve"),
#             ("Actual Power Curve", "actual_power_curve"),
#             ("Binned Power Curve", "binned_power_curve"),
#             ("Rotor Speed Analysis", "rotor_speed_graph"),
#             ("Power vs Generator Temp", "power_vs_generator_temperature"),
#             ("Rotor Speed vs Gearbox Temp", "rotor_speed_vs_gearbox_temperature"),
#             ("Ambient vs Nacelle Temp", "ambient_vs_nacelle_temperature"),
#             ("Rotor Speed vs Gen Speed", "rotor_speed_vs_generator_speed"),
#             ("Joint Distribution", "joint_distribution")
#         ]
        
#         for plot_name, plot_type in plot_types:
#             cb = QCheckBox(plot_name)
#             cb.setChecked(True)
#             scroll_layout.addWidget(cb)
#             checkboxes[plot_type] = cb
        
#         scroll_layout.addStretch()
#         scroll_widget.setLayout(scroll_layout)
#         scroll.setWidget(scroll_widget)
#         main_layout.addWidget(scroll, 1)
        
#         # --- Footer Buttons ---
#         sep2 = QFrame()
#         sep2.setObjectName("separator")
#         sep2.setFrameShape(QFrame.HLine)
#         sep2.setFixedHeight(1)
#         main_layout.addWidget(sep2)
        
#         button_frame = QFrame()
#         button_frame.setStyleSheet("QFrame { background-color: #233140; }")
#         button_frame.setFixedHeight(90)
        
#         button_layout = QHBoxLayout()
#         button_layout.setSpacing(15)
#         button_layout.setContentsMargins(20, 15, 20, 15)
        
#         select_all_btn = QPushButton("Select All")
#         select_all_btn.setObjectName("secondary")
        
#         select_none_btn = QPushButton("Deselect All")
#         select_none_btn.setObjectName("secondary")
        
#         cancel_btn = QPushButton("Cancel")
#         cancel_btn.setObjectName("secondary")
        
#         ok_btn = QPushButton("Generate Report")
        
#         button_layout.addWidget(select_all_btn)
#         button_layout.addWidget(select_none_btn)
#         button_layout.addStretch()
#         button_layout.addWidget(cancel_btn)
#         button_layout.addWidget(ok_btn)
        
#         button_frame.setLayout(button_layout)
#         main_layout.addWidget(button_frame)
        
#         dialog.setLayout(main_layout)
        
#         # Connect signals
#         select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes.values()])
#         select_none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes.values()])
#         ok_btn.clicked.connect(dialog.accept)
#         cancel_btn.clicked.connect(dialog.reject)
        
#         if dialog.exec_() == QDialog.Accepted:
#             return {plot_type: cb.isChecked() for plot_type, cb in checkboxes.items()}
#         else:
#             return None


# # Usage in your main class:
# def generate_report(self):
#     """Enhanced report generation method for the main class."""
#     generator = EnhancedReportGenerator(self)
#     generator.generate_report()

import os
import traceback
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.table as mplt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, 
                              PageBreak, Table, TableStyle, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from views.visualization_components.plotting_logic import plot_selected_graph

class EnhancedReportGenerator:
    """Enhanced report generator with comprehensive features and better organization."""
    
    def __init__(self, parent):
        self.parent = parent
        self.temp_dir = None
        self.progress_dialog = None

    def _get_project_info(self):
        """Get project information from database."""
        try:
            if hasattr(self.parent, 'project_id'):
                from controllers.database.database_manager import DatabaseManager
                db = DatabaseManager()
                cursor = db.connection.execute(
                    "SELECT project_name, location, company, capacity, model_name FROM Projects WHERE project_id = ?",
                    [self.parent.project_id]
                )
                row = cursor.fetchone()
                db.close()
                
                if row:
                    return {
                        'name': row[0],
                        'location': row[1],
                        'company': row[2],
                        'capacity': row[3],
                        'model_name': row[4]
                    }
        except Exception as e:
            print(f"Error getting project info: {e}")
        
        return {}

    def generate_report(self):
        """Generate a comprehensive PDF report with enhanced features and user plot support."""
        try:
            if self.parent.data is None or self.parent.data.empty:
                self.parent.handle_errors("No data available to generate report.")
                return

            # Show plot selection dialog
            selected_plots = self._create_plot_selection_dialog()
            if selected_plots is None:  # User cancelled
                return

            # Setup progress dialog
            self.progress_dialog = QProgressDialog("Generating report...", "Cancel", 0, 100, self.parent)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.show()
          
            # Get save location
            # turbine_id = self.turbine_id or 'Unknown'
            turbine_id = getattr(self.parent, 'turbine_name', None) or getattr(self.parent, 'windowTitle', lambda: 'Unknown')().split(': ')[-1] if ': ' in getattr(self.parent, 'windowTitle', lambda: 'Unknown')() else 'Unknown'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Wind_Turbine_Report_{turbine_id}_{timestamp}.pdf"
            
            file_name, _ = QFileDialog.getSaveFileName(
                self.parent, "Save Report", default_filename, "PDF Files (*.pdf)"
            )
            
            if not file_name:
                self.parent.statusBar.showMessage("Report generation cancelled.", 5000)
                return

            # Initialize temporary directory
            self._setup_temp_directory(file_name)
            
            # Generate report sections
            self._update_progress(10, "Generating metadata...")
            metadata = self._generate_metadata()
            
            self._update_progress(20, "Creating plots...")
            plot_images = self._generate_plot_images_with_selection(selected_plots)
            
            self._update_progress(60, "Creating tables...")
            table_images = self._generate_table_images()
            
            self._update_progress(80, "Assembling PDF...")
            self._create_pdf_report(file_name, metadata, plot_images, table_images)
            
            self._update_progress(95, "Cleaning up...")
            self._cleanup_temp_files()
            
            self._update_progress(100, "Complete!")
            self.progress_dialog.close()
            
            # Success message with detailed info
            plot_count = len(plot_images)
            custom_plot_count = len([p for p in plot_images if 'custom' in p[1].lower() or 'modified' in p[1].lower() or 'current' in p[1].lower()])
            
            success_msg = f"""Comprehensive report successfully generated!

                Location: {file_name}
                Total Plots: {plot_count}
                Custom/Modified Plots: {custom_plot_count}
                Data Tables: {len(table_images)}
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                The report includes your custom modifications and user-drawn plots."""
            
            self.parent.statusBar.showMessage(f"Report successfully generated with {plot_count} plots", 5000)
            QMessageBox.information(self.parent, "Success", success_msg)
            
        except Exception as e:
            if self.progress_dialog:
                self.progress_dialog.close()
            self._cleanup_temp_files()
            self.parent.handle_errors(f"Error generating report: {str(e)}\n{traceback.format_exc()}")
            self.parent.statusBar.showMessage("Error generating report.", 5000)
    
    def _generate_plot_images_with_selection(self, selected_plots):
        """Generate plot images based on user selection."""
        plot_images = []
        
        # # Line 28: Debug parent type
        # print(f"Parent type: {type(self.parent).__name__}")
        
        # Add current plot if selected
        if selected_plots.get('current_plot', False):
            current_plot = self._capture_current_plot()
            if current_plot:
                plot_images.append(current_plot)
        
        # Add custom plots if selected
        if selected_plots.get('custom_plots', False):
            custom_plots = self._get_user_custom_plots()
            plot_images.extend(custom_plots)
        
        # Generate standard plots based on selection
        plot_types = [
            ("Wind Rose", "wind_rose"),
            ("Wind Speed Distribution", "wind_speed_distribution"),
            ("Turbulence Intensity", "turbulence_intensity"),
            ("Wind Frequency Histogram", "wind_frequency_histogram"),
            ("Power Curve", "power_curve"),
            ("Actual Power Curve", "actual_power_curve"),
            ("Binned Power Curve", "binned_power_curve"),
            ("Rotor Speed Analysis", "rotor_speed_graph"),
            ("Rotor Speed vs Gearbox Temperature", "rotor_speed_vs_gearbox_temperature"),
            ("Ambient vs Nacelle Temperature", "ambient_vs_nacelle_temperature"),
            ("Rotor Speed vs Generator Speed", "rotor_speed_vs_generator_speed"),
            ("Joint Distribution", "joint_distribution")
        ]
        
        original_figure = self.parent.figure
        original_plot = self.parent.selected_plot
        
        for i, (plot_name, plot_type) in enumerate(plot_types):
            if not selected_plots.get(plot_type, False):
                continue
                
            try:
                progress = 20 + (i / len(plot_types)) * 40
                self._update_progress(int(progress), f"Creating {plot_name}...")
                
                cached_plot = self._get_cached_user_plot(plot_type)
                if cached_plot:
                    plot_images.append(cached_plot)
                    continue
                
                self.parent.selected_plot = plot_type
                self.parent.filtered_df = self.parent.get_filtered_data()
                
                if self.parent.filtered_df.empty:
                    plot_images.append(self._create_error_plot(plot_name, "No data available"))
                    continue
                
                # # Line 79: Debug data details
                # print(f"Plot type: {plot_type}")
                # print(f"Filtered data columns: {self.parent.filtered_df.columns.tolist()}")
                # print(f"Column cache: {getattr(self.parent, 'column_cache', 'Not available')}")
                
                new_fig = Figure(figsize=(10, 7))
                self.parent.figure = new_fig
                
                # Line 87: Use direct plot_selected_graph import
                plot_functions = {
                    plot_type: lambda vw: plot_selected_graph(vw, plot_type, vw.column_cache)
                }
                plot_functions[plot_type](self.parent)
                
                self._enhance_plot_appearance(new_fig)
                
                image_path = os.path.join(self.temp_dir, f"{plot_type}.png")
                new_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                plt.close(new_fig)
                
                plot_images.append((plot_name, image_path, self._get_plot_description(plot_type)))
                
            except Exception as e:
                # Line 101: Enhanced error logging
                error_msg = f"Error generating plot {plot_type}: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                plot_images.append(self._create_error_plot(plot_name, error_msg))
        
        self.parent.figure = original_figure
        self.parent.selected_plot = original_plot
        self.parent.update_plot_signal.emit()
        
        return plot_images

    def _cleanup_temp_files(self):
        """Clean up temporary files and directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def _update_progress(self, value, message):
        """Update progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(message)
            if self.progress_dialog.wasCanceled():
                raise Exception("Report generation cancelled by user")
    
    def _setup_temp_directory(self, file_name):
        """Setup temporary directory for images."""
        self.temp_dir = os.path.join(os.path.dirname(file_name), f"temp_report_{datetime.now().strftime('%H%M%S')}")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _generate_metadata(self):
        """Generate comprehensive metadata for the report."""
        data = self.parent.data
        # turbine_id = self.turbine_id if self.turbine_id else getattr(self.parent, 'turbine_id', 'Unknown')    
        turbine_id = getattr(self.parent, 'turbine_name', None) or (getattr(self.parent, 'windowTitle', lambda: 'Unknown')().split(': ')[-1] if ': ' in getattr(self.parent, 'windowTitle', lambda: 'Unknown')() else 'Unknown')
        total_records = len(data)
        date_range = None
        if 'timestamp' in data.columns:
            date_range = f"{data['timestamp'].min()} to {data['timestamp'].max()}"
        
        missing_data = data.isnull().sum().sum()
        data_completeness = ((total_records * len(data.columns) - missing_data) / 
                        (total_records * len(data.columns)) * 100)
        
        wind_stats = {}
        if 'wind_speed' in data.columns:
            wind_data = data['wind_speed'].dropna()
            wind_stats = {
                'mean_wind_speed': wind_data.mean(),
                'max_wind_speed': wind_data.max(),
                'min_wind_speed': wind_data.min(),
                'wind_speed_std': wind_data.std(),
                'wind_speed_95th': wind_data.quantile(0.95),
                'wind_speed_median': wind_data.median()
            }
        
        power_stats = {}
        if 'power' in data.columns:
            power_data = data['power'].dropna()
            if len(power_data) > 0:
                max_power = power_data.max()
                power_stats = {
                    'mean_power': power_data.mean(),
                    'max_power': max_power,
                    'total_energy': power_data.sum() / (1000 * 24) if len(power_data) > 24 else power_data.sum() / 1000,
                    'capacity_factor': (power_data.mean() / max_power * 100) if max_power > 0 else 0,
                    'power_std': power_data.std(),
                    'operational_hours': len(power_data[power_data > 0])
                }
        
        return {
            'turbine_id': turbine_id,
            'data_period': date_range,
            'total_records': total_records,
            'data_completeness': data_completeness,
            'missing_data_points': missing_data,
            'wind_statistics': wind_stats,
            'power_statistics': power_stats,
            'columns': list(data.columns),
        }
        
    def _generate_plot_images(self):
        """Generate plot images for all available plot types."""
        plot_images = []
        
        # Line 116: Debug parent type
        print(f"Parent type: {type(self.parent).__name__}")
        
        plot_types = [
            ("Wind Rose", "wind_rose"),
            ("Wind Speed Distribution", "wind_speed_distribution"),
            ("Turbulence Intensity", "turbulence_intensity"),
            ("Wind Frequency Histogram", "wind_frequency_histogram"),
            ("Power Curve", "power_curve"),
            ("Actual Power Curve", "actual_power_curve"),
            ("Binned Power Curve", "binned_power_curve"),
            ("Rotor Speed Analysis", "rotor_speed_graph"),
            ("Power vs Generator Temperature", "power_vs_generator_temperature"),
            ("Rotor Speed vs Gearbox Temperature", "rotor_speed_vs_gearbox_temperature"),
            ("Ambient vs Nacelle Temperature", "ambient_vs_nacelle_temperature"),
            ("Rotor Speed vs Generator Speed", "rotor_speed_vs_generator_speed"),
            ("Joint Distribution", "joint_distribution")
        ]
        
        original_figure = self.parent.figure
        original_plot = self.parent.selected_plot
        
        for i, (plot_name, plot_type) in enumerate(plot_types):
            try:
                progress = 20 + (i / len(plot_types)) * 40
                self._update_progress(int(progress), f"Creating {plot_name}...")
                
                self.parent.selected_plot = plot_type
                self.parent.filtered_df = self.parent.get_filtered_data()
                
                if self.parent.filtered_df.empty:
                    plot_images.append(self._create_error_plot(plot_name, "No data available"))
                    continue
                
                # Line 150: Debug data details
                print(f"Plot type: {plot_type}")
                print(f"Filtered data columns: {self.parent.filtered_df.columns.tolist()}")
                print(f"Column cache: {getattr(self.parent, 'column_cache', 'Not available')}")
                
                new_fig = Figure(figsize=(10, 7))
                self.parent.figure = new_fig
                
                # Line 158: Use direct plot_selected_graph import
                plot_functions = {
                    plot_type: lambda vw: plot_selected_graph(vw, plot_type, vw.column_cache)
                }
                plot_functions[plot_type](self.parent)
                
                self._enhance_plot_appearance(new_fig)
                
                image_path = os.path.join(self.temp_dir, f"{plot_type}.png")
                new_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                plt.close(new_fig)
                
                plot_images.append((plot_name, image_path, self._get_plot_description(plot_type)))
                
            except Exception as e:
                # Line 172: Enhanced error logging
                error_msg = f"Error generating plot {plot_type}: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                plot_images.append(self._create_error_plot(plot_name, error_msg))
        
        self.parent.figure = original_figure
        self.parent.selected_plot = original_plot
        self.parent.update_plot_signal.emit()
        
        return plot_images
    
    def _enhance_plot_appearance(self, fig):
        """Enhance plot appearance with professional styling."""
        fig.patch.set_facecolor('white')
        fig.patch.set_edgecolor('black')
        fig.patch.set_linewidth(1.5)
        
        for ax in fig.axes:
            ax.set_facecolor('white')
            
            # Professional grid styling
            ax.grid(True, color='#D0D0D0', linestyle='-', linewidth=0.6, alpha=0.7, zorder=0)
            ax.set_axisbelow(True)
            
            # Enhanced frame styling - show all spines with professional appearance
            for spine_name in ax.spines:
                ax.spines[spine_name].set_visible(True)
                ax.spines[spine_name].set_color('#333333')
                ax.spines[spine_name].set_linewidth(1.2)
            
            # Professional tick styling
            ax.tick_params(colors='#2E2E2E', labelsize=11, direction='out', 
                        length=5, width=1.1, pad=4)
            ax.tick_params(which='minor', colors='#2E2E2E', direction='out', 
                        length=3, width=0.8)
            
            # Enhanced axis labels
            if hasattr(ax, 'xaxis') and hasattr(ax.xaxis, 'label'):
                ax.xaxis.label.set_color('#1A1A1A')
                ax.xaxis.label.set_fontsize(13)
                ax.xaxis.label.set_fontweight('bold')
                ax.xaxis.label.set_fontfamily('serif')
            
            if hasattr(ax, 'yaxis') and hasattr(ax.yaxis, 'label'):
                ax.yaxis.label.set_color('#1A1A1A')
                ax.yaxis.label.set_fontsize(13)
                ax.yaxis.label.set_fontweight('bold')
                ax.yaxis.label.set_fontfamily('serif')
            
            # Professional title styling
            if hasattr(ax, 'title') and ax.title.get_text():
                ax.title.set_color('#0D47A1')
                ax.title.set_fontsize(16)
                ax.title.set_fontweight('bold')
                ax.title.set_fontfamily('serif')
                ax.set_title(ax.get_title(), pad=20)
            
            # Enhanced legend styling
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor('#F8F9FA')
                legend.get_frame().set_edgecolor('#333333')
                legend.get_frame().set_linewidth(1.0)
                legend.get_frame().set_alpha(0.95)
                legend.get_frame().set_boxstyle("round,pad=0.5")
                legend.set_title(legend.get_title().get_text(), prop={'weight': 'bold', 'size': 11})
                for text in legend.get_texts():
                    text.set_color('#1A1A1A')
                    text.set_fontsize(11)
                    text.set_fontfamily('serif')
            
            # Add professional plot margins
            ax.margins(x=0.02, y=0.02)
        
        # Ensure tight layout with proper spacing
        fig.tight_layout(pad=2.0)

    def _create_error_plot(self, plot_name, error_msg):
        """Create placeholder plot for errors."""
        fig = Figure(figsize=(10, 7))
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, f"Plot Not Available\n\n{plot_name}\n\nReason: {error_msg}", 
                ha='center', va='center', fontsize=12, color='red',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        
        image_path = os.path.join(self.temp_dir, f"error_{plot_name.replace(' ', '_')}.png")
        fig.savefig(image_path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        
        return (plot_name, image_path, "Plot could not be generated due to data issues.")
    
    def _get_plot_description(self, plot_type):
        """Get description for each plot type."""
        descriptions = {
            'wind_rose': "Wind rose diagram showing wind direction frequency and speed distribution.",
            'wind_speed_distribution': "Statistical distribution of wind speeds over the analysis period.",
            'turbulence_intensity': "Turbulence intensity analysis showing wind variability characteristics.",
            'power_curve': "Theoretical power curve showing expected power output vs wind speed.",
            'actual_power_curve': "Actual measured power curve compared to theoretical values.",
            'binned_power_curve': "Binned power curve analysis for performance assessment.",
            'rotor_speed_graph': "Rotor speed variations and operational characteristics.",
            'rotor_speed_vs_gearbox_temperature': "Relationship between rotor speed and gearbox thermal behavior.",
            'ambient_vs_nacelle_temperature': "Temperature differential analysis between ambient and nacelle.",
            'rotor_speed_vs_generator_speed': "Gearbox ratio analysis and mechanical efficiency.",
            'joint_distribution': "Multi-variable distribution analysis of key parameters."
        }
        return descriptions.get(plot_type, "Analysis of turbine operational parameters.")
    
    def _generate_table_images(self):
        """Generate table images with enhanced formatting."""
        tables = [
            ("Executive Summary", self.parent.summary_table),
            ("Statistical Analysis", self.parent.stats_table),
            ("Bin Analysis Records", getattr(self.parent, 'bin_table', None)),
            ("Performance Bands", getattr(self.parent, 'percentage_bands_table', None) 
             if getattr(self.parent, 'enable_percentage_bands', False) and 
             hasattr(self.parent, 'enable_percentage_bands') and 
             self.parent.enable_percentage_bands.isChecked() else None),
            ("Standard Power Data", self.parent.standard_data_table),
            ("Filtered Data Records", getattr(self.parent, 'removed_data_table', None)
             if getattr(self.parent, 'remove_negative_power', False) and 
             hasattr(self.parent, 'remove_negative_power') and 
             self.parent.remove_negative_power.isChecked() else None)
        ]
        
        table_images = []
        for table_name, table in tables:
            if table is None:
                continue
                
            try:
                # Create enhanced table image
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.axis('off')
                
                # Extract table data
                data = []
                headers = []
                
                # Get headers
                for col in range(table.columnCount()):
                    header_item = table.horizontalHeaderItem(col)
                    headers.append(header_item.text() if header_item else f"Col {col}")
                
                # Get data
                for row in range(min(table.rowCount(), 50)):  # Limit rows for readability
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
                
                if data:  # Only create table if there's data
                    # Create table
                    table_plot = ax.table(cellText=data, colLabels=headers, 
                                        loc='center', cellLoc='center')
                    
                    # Style the table
                    table_plot.auto_set_font_size(False)
                    table_plot.set_fontsize(8)
                    table_plot.scale(1, 2)
                    
                    # Style headers
                    for i in range(len(headers)):
                        table_plot[(0, i)].set_facecolor('#4472C4')
                        table_plot[(0, i)].set_text_props(weight='bold', color='white')
                    
                    # Alternate row colors
                    for i in range(1, len(data) + 1):
                        for j in range(len(headers)):
                            if i % 2 == 0:
                                table_plot[(i, j)].set_facecolor('#F2F2F2')
                            else:
                                table_plot[(i, j)].set_facecolor('white')
                
                # Add title
                plt.title(table_name, fontsize=14, fontweight='bold', pad=20)
                
                # Save table image
                image_path = os.path.join(self.temp_dir, f"{table_name.replace(' ', '_')}.png")
                fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                plt.close(fig)
                
                table_images.append((table_name, image_path))
                
            except Exception as e:
                print(f"Error generating table {table_name}: {e}")
                continue
        
        return table_images
    
    def _create_pdf_report(self, file_name, metadata, plot_images, table_images):
        """Create comprehensive PDF report with enhanced professional layout."""
        doc = SimpleDocTemplate(file_name, pagesize=A4, 
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()       
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                fontSize=26, spaceAfter=30, alignment=TA_CENTER,
                                textColor=colors.HexColor('#1565C0'), fontName='Helvetica-Bold')
        
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                    fontSize=16, spaceAfter=18, spaceBefore=24,
                                    textColor=colors.HexColor('#1976D2'), fontName='Helvetica-Bold')
        subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'],
                                        fontSize=14, spaceAfter=12, spaceBefore=16,
                                        textColor=colors.HexColor('#424242'), fontName='Helvetica-Bold')
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                    fontSize=11, spaceAfter=12, alignment=TA_LEFT,
                                    fontName='Helvetica', leading=14)
        caption_style = ParagraphStyle('Caption', parent=styles['Normal'],
                                    fontSize=9, spaceAfter=8, alignment=TA_CENTER,
                                    textColor=colors.HexColor('#666666'),
                                    fontName='Helvetica-Oblique')
        
        elements.extend(self._create_title_page(metadata, title_style, heading_style, normal_style))
        elements.append(PageBreak())
        elements.extend(self._create_table_of_contents(plot_images, table_images, heading_style, normal_style))
        elements.append(PageBreak())
        elements.extend(self._create_executive_summary(metadata, heading_style, normal_style))
        elements.append(PageBreak())
        elements.append(Paragraph("Performance Analysis & Visualizations", heading_style))
        elements.append(Spacer(1, 0.3*inch))
        
        for i, (plot_name, image_path, description) in enumerate(plot_images):
            elements.append(KeepTogether([
                Paragraph(f"{i+1}. {plot_name}", subheading_style),
                Spacer(1, 0.15*inch),
                Image(image_path, width=7*inch, height=4.9*inch),
                Spacer(1, 0.1*inch),
                Paragraph(f"Figure {i+1}: {description}", caption_style),
                Spacer(1, 0.25*inch)
            ]))
            
            if (i + 1) % 2 == 0 and i < len(plot_images) - 1:
                elements.append(PageBreak())
        
        if table_images:
            elements.append(PageBreak())
            elements.append(Paragraph("Statistical Data Tables", heading_style))
            elements.append(Spacer(1, 0.3*inch))
            
            for i, (table_name, image_path) in enumerate(table_images):
                elements.append(KeepTogether([
                    Paragraph(f"{i+1}. {table_name}", subheading_style),
                    Spacer(1, 0.15*inch),
                    Image(image_path, width=7.5*inch, height=5*inch),
                    Spacer(1, 0.25*inch)
                ]))
        
        elements.append(PageBreak())
        elements.extend(self._create_report_footer(metadata, normal_style))
        
        doc.build(elements)
    
    # def _create_title_page(self, metadata, title_style, heading_style, normal_style):
    #     """Create professional title page."""
    #     elements = []
        
    #     project_title = getattr(self.parent, 'project_title', None)
    #     if not project_title:
    #         project_title = getattr(self.parent, 'project_file_name', 'Wind Turbine Performance Analysis')
    
    #     turbine_id = metadata.get('turbine_id', 'Unknown')
    #     elements.append(Spacer(1, 1.5*inch))
    #     elements.append(Paragraph(f"{project_title}", title_style))
    #     elements.append(Spacer(1, 0.3*inch))
    #     elements.append(Paragraph(f"Turbine ID: {turbine_id}", heading_style))
    #     elements.append(Spacer(1, 0.5*inch))
        
    #     report_data = [
    #         ['Analysis Period:', metadata.get('data_period', 'Full Dataset')],
    #         ['Total Data Points:', f"{metadata['total_records']:,}"],
    #         ['Data Quality:', f"{metadata['data_completeness']:.1f}% Complete"],
    #         ['Analyzed Parameters:', f"{len(metadata['columns'])} Columns"]
    #     ]
        
    #     report_table = Table(report_data, colWidths=[2.2*inch, 3.3*inch])
    #     report_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1565C0')),
    #         ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8F9FA')),
    #         ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
    #         ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    #         ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    #         ('FONTSIZE', (0, 0), (-1, -1), 11),
    #         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #         ('LEFTPADDING', (0, 0), (-1, -1), 8),
    #         ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    #         ('TOPPADDING', (0, 0), (-1, -1), 6),
    #         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    #     ]))
        
    #     elements.append(report_table)
    #     elements.append(Spacer(1, 0.8*inch))
        
    #     if metadata['wind_statistics']:
    #         ws = metadata['wind_statistics']
    #         elements.append(Paragraph("Wind Characteristics Summary", heading_style))
    #         wind_summary_data = [
    #             ['Mean Wind Speed:', f"{ws.get('mean_wind_speed', 0):.2f} m/s"],
    #             ['Maximum Wind Speed:', f"{ws.get('max_wind_speed', 0):.2f} m/s"],
    #             ['95th Percentile:', f"{ws.get('wind_speed_95th', 0):.2f} m/s"],
    #             ['Standard Deviation:', f"{ws.get('wind_speed_std', 0):.2f} m/s"]
    #         ]
    #         wind_table = Table(wind_summary_data, colWidths=[2.2*inch, 3.3*inch])
    #         wind_table.setStyle(TableStyle([
    #             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#388E3C')),
    #             ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F1F8E9')),
    #             ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
    #             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    #             ('FONTSIZE', (0, 0), (-1, -1), 10),
    #             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    #             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #             ('LEFTPADDING', (0, 0), (-1, -1), 8),
    #             ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    #         ]))
    #         elements.append(wind_table)
    #         elements.append(Spacer(1, 0.3*inch))
        
    #     if metadata['power_statistics']:
    #         ps = metadata['power_statistics']
    #         elements.append(Paragraph("Power Performance Summary", heading_style))
    #         power_summary_data = [
    #             ['Average Power Output:', f"{ps.get('mean_power', 0):.2f} kW"],
    #             ['Maximum Power Output:', f"{ps.get('max_power', 0):.2f} kW"],
    #             ['Estimated Energy Production:', f"{ps.get('total_energy', 0):.2f} MWh"],
    #             ['Capacity Factor:', f"{ps.get('capacity_factor', 0):.1f}%"],
    #             ['Operational Hours:', f"{ps.get('operational_hours', 0):,}"]
    #         ]
    #         power_table = Table(power_summary_data, colWidths=[2.2*inch, 3.3*inch])
    #         power_table.setStyle(TableStyle([
    #             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F57C00')),
    #             ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FFF8E1')),
    #             ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
    #             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    #             ('FONTSIZE', (0, 0), (-1, -1), 10),
    #             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    #             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #             ('LEFTPADDING', (0, 0), (-1, -1), 8),
    #             ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    #         ]))
    #         elements.append(power_table)
        
    #     return elements
    
    def _create_title_page(self, metadata, title_style, heading_style, normal_style):
        """Create professional title page."""
        elements = []
        
        # Get project info from database
        project_info = self._get_project_info()
        
        project_title = project_info.get('name', 'Wind Turbine Performance Analysis')
        turbine_id = metadata.get('turbine_id', 'Unknown')
        
        elements.append(Spacer(1, 1.5*inch))
        elements.append(Paragraph(f"{project_title}", title_style))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(f"Turbine ID: {turbine_id}", heading_style))
        elements.append(Spacer(1, 0.5*inch))
        
        report_data = [
            ['Project Name:', project_info.get('name', 'N/A')],
            ['Company:', project_info.get('company', 'N/A')],
            ['Location:', project_info.get('location', 'N/A')],
            ['Capacity:', project_info.get('capacity', 'N/A')],
            ['Model:', project_info.get('model_name', 'N/A')],
            ['Analysis Period:', metadata.get('data_period', 'Full Dataset')],
            ['Total Data Points:', f"{metadata['total_records']:,}"],
            ['Data Quality:', f"{metadata['data_completeness']:.1f}% Complete"]
        ]
        
        report_table = Table(report_data, colWidths=[2.2*inch, 3.3*inch])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1565C0')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(report_table)
        elements.append(Spacer(1, 0.8*inch))
        return elements
    
    def _create_table_of_contents(self, plot_images, table_images, heading_style, normal_style):
        """Create table of contents."""
        elements = []
        elements.append(Paragraph("Table of Contents", heading_style))
        elements.append(Spacer(1, 0.3*inch))
        
        toc_data = [
            ['Section', 'Page'],
            ['Executive Summary', '3'],
            ['Data Analysis & Visualizations', '4']
        ]
        
        # page_num = 5
        # for plot_name, _, _ in plot_images[:5]:  # Show first 5 plots
        #     toc_data.append([f"  • {plot_name}", str(page_num)])
        #     page_num += 1
        
        # if len(plot_images) > 5:
        #     toc_data.append([f"  • ... and {len(plot_images)-5} more plots", "..."])
        
        page_num = 5
        for plot_name, _, _ in plot_images:  # Show ALL plots
            toc_data.append([f"  • {plot_name}", str(page_num)])
            page_num += 1

        if table_images:
            toc_data.append(['Data Tables & Statistics', str(page_num)])
        
        toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(toc_table)
        return elements
    
    def _create_executive_summary(self, metadata, heading_style, normal_style):
        """Create comprehensive executive summary section."""
        elements = []
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        summary_text = f"""
        This comprehensive performance analysis report provides detailed insights into the operational 
        characteristics of Wind Turbine {metadata['turbine_id']} based on {metadata['total_records']:,} 
        data records collected over {metadata.get('data_period', 'the analysis period')}. The dataset 
        demonstrates {metadata['data_completeness']:.1f}% completeness, ensuring reliable statistical analysis.
        """
        
        elements.append(Paragraph(summary_text, normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        key_findings = []
        
        if metadata['wind_statistics']:
            ws = metadata['wind_statistics']
            wind_finding = f"""
            <b>Wind Resource Assessment:</b> The site experienced an average wind speed of 
            {ws.get('mean_wind_speed', 0):.2f} m/s with maximum recorded speeds reaching 
            {ws.get('max_wind_speed', 0):.2f} m/s. Wind variability, measured by standard deviation 
            ({ws.get('wind_speed_std', 0):.2f} m/s), indicates {'moderate' if ws.get('wind_speed_std', 0) < 3 else 'high'} 
            turbulence characteristics typical for this wind regime.
            """
            key_findings.append(wind_finding)
        
        if metadata['power_statistics']:
            ps = metadata['power_statistics']
            cf = ps.get('capacity_factor', 0)
            cf_rating = 'excellent' if cf > 40 else 'good' if cf > 30 else 'moderate' if cf > 20 else 'low'
            
            power_finding = f"""
            <b>Power Performance:</b> The turbine achieved an average power output of 
            {ps.get('mean_power', 0):.2f} kW with a capacity factor of {cf:.1f}%, indicating 
            {cf_rating} performance relative to industry standards. Total estimated energy 
            production reached {ps.get('total_energy', 0):.2f} MWh during the analysis period.
            """
            key_findings.append(power_finding)
        
        data_quality_finding = f"""
        <b>Data Quality Assessment:</b> The analysis is based on high-quality data with 
        {metadata['data_completeness']:.1f}% completeness. Missing data points 
        ({metadata['missing_data_points']:,} out of {metadata['total_records'] * len(metadata['columns']):,}) 
        have been appropriately handled to ensure statistical validity.
        """
        key_findings.append(data_quality_finding)
        
        for finding in key_findings:
            elements.append(Paragraph(finding, normal_style))
            elements.append(Spacer(1, 0.15*inch))
        
        recommendations = """
        <b>Report Structure:</b> This report presents comprehensive visualizations including wind 
        resource analysis, power performance curves, temperature correlations, and operational 
        parameter relationships. Each visualization is accompanied by detailed descriptions and 
        statistical interpretations to support engineering decision-making and performance optimization.
        """
        
        elements.append(Paragraph(recommendations, normal_style))
        return elements
    
    def _create_report_footer(self, metadata, normal_style):
        """Create report footer with additional information."""
        elements = []
        
        footer_text = f"""
        <b>Report Information</b><br/>
        Data columns analyzed: {len(metadata['columns'])}<br/>
        Total data points: {metadata['total_records']:,}<br/>
        Missing data points: {metadata['missing_data_points']:,}<br/>
        
        <b>Disclaimer</b><br/>
        This report is generated based on the provided data and should be used in conjunction with 
        engineering judgment and site-specific knowledge. All measurements and calculations are 
        subject to instrumentation accuracy and data quality limitations.
        """
        
        elements.append(Paragraph(footer_text, normal_style))
        return elements
    
    def _capture_current_plot(self):
        """Capture the currently displayed plot if it's user-modified."""
        try:
            if self.parent.figure and hasattr(self.parent.figure, 'axes') and self.parent.figure.axes:
                # Check if the current plot has been modified by looking for custom elements
                current_plot_type = getattr(self.parent, 'selected_plot', 'current_plot')
                
                # Create a copy of the current figure
                current_fig = self.parent.figure
                
                # Save the current plot
                image_path = os.path.join(self.temp_dir, f"current_user_plot_{current_plot_type}.png")
                current_fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                
                plot_name = f"Current Plot ({current_plot_type.replace('_', ' ').title()})"
                description = "User's currently displayed plot with any modifications applied."
                
                return (plot_name, image_path, description)
        except Exception as e:
            print(f"Error capturing current plot: {e}")
        return None
    
    def _get_user_custom_plots(self):
        """Get user-saved custom plots from various sources."""
        custom_plots = []
        
        try:
            # Check if parent has a custom plots storage
            if hasattr(self.parent, 'custom_plots') and self.parent.custom_plots:
                for plot_name, plot_data in self.parent.custom_plots.items():
                    if isinstance(plot_data, dict) and 'figure' in plot_data:
                        image_path = os.path.join(self.temp_dir, f"custom_{plot_name.replace(' ', '_')}.png")
                        plot_data['figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                        description = plot_data.get('description', 'User-created custom plot')
                        custom_plots.append((plot_name, image_path, description))
            
            # Check for matplotlib figures stored in parent
            if hasattr(self.parent, 'saved_figures') and self.parent.saved_figures:
                for i, (fig, metadata) in enumerate(self.parent.saved_figures):
                    plot_name = metadata.get('name', f'Custom Plot {i+1}')
                    image_path = os.path.join(self.temp_dir, f"saved_figure_{i}.png")
                    fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                    description = metadata.get('description', 'User-saved custom figure')
                    custom_plots.append((plot_name, image_path, description))
            
            # Check for plot modifications cache
            if hasattr(self.parent, 'plot_modifications') and self.parent.plot_modifications:
                for plot_type, modifications in self.parent.plot_modifications.items():
                    if 'modified_figure' in modifications:
                        plot_name = f"Modified {plot_type.replace('_', ' ').title()}"
                        image_path = os.path.join(self.temp_dir, f"modified_{plot_type}.png")
                        modifications['modified_figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                        description = f"User-modified version of {plot_type} with custom adjustments"
                        custom_plots.append((plot_name, image_path, description))
                        
        except Exception as e:
            print(f"Error getting user custom plots: {e}")
        
        return custom_plots
    
    def _get_cached_user_plot(self, plot_type):
        """Get cached user-modified version of a specific plot type."""
        try:
            # Check if user has cached modifications for this plot type
            if hasattr(self.parent, 'plot_cache') and plot_type in self.parent.plot_cache:
                cached_data = self.parent.plot_cache[plot_type]
                
                if 'figure' in cached_data:
                    plot_name = cached_data.get('name', plot_type.replace('_', ' ').title())
                    image_path = os.path.join(self.temp_dir, f"cached_{plot_type}.png")
                    cached_data['figure'].savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                    description = cached_data.get('description', f'Cached user version of {plot_type}')
                    return (plot_name, image_path, description)
            
            # Check if there's a user-modified canvas for this plot type
            if hasattr(self.parent, 'canvas') and hasattr(self.parent.canvas, 'figure'):
                # Check if current canvas figure matches the plot type we're looking for
                current_selected = getattr(self.parent, 'selected_plot', None)
                if current_selected == plot_type:
                    # Check if the figure has been modified (has custom annotations, etc.)
                    fig = self.parent.canvas.figure
                    if self._is_figure_modified(fig):
                        plot_name = f"Modified {plot_type.replace('_', ' ').title()}"
                        image_path = os.path.join(self.temp_dir, f"user_modified_{plot_type}.png")
                        fig.savefig(image_path, bbox_inches='tight', dpi=300, facecolor='white')
                        description = f'User-modified {plot_type} with custom elements'
                        return (plot_name, image_path, description)
                        
        except Exception as e:
            print(f"Error getting cached user plot for {plot_type}: {e}")
        
        return None
    
    def _is_figure_modified(self, fig):
        """Check if a figure has been modified by the user."""
        try:
            # Check for custom annotations, text, or additional elements
            for ax in fig.axes:
                # Check for user-added text annotations
                if hasattr(ax, 'texts') and len(ax.texts) > 0:
                    for text in ax.texts:
                        # Check if text is not a default axis label
                        if text.get_text() and not any(label in text.get_text().lower() 
                                                     for label in ['xlabel', 'ylabel', 'title']):
                            return True
                
                # Check for user-added lines or patches
                if hasattr(ax, 'lines') and len(ax.lines) > 1:  # More than just data lines
                    return True
                # Check for custom patches (shapes, rectangles, etc.)
                if hasattr(ax, 'patches') and len(ax.patches) > 0:
                    return True
                # Check for custom collections (scatter plots, etc.)
                if hasattr(ax, 'collections') and len(ax.collections) > 1:
                    return True
            # Check for custom figure-level elements
            if hasattr(fig, 'texts') and len(fig.texts) > 0:
                return True
        except Exception as e:
            print(f"Error checking if figure is modified: {e}")
        return False
    def _save_user_plot_for_future(self, plot_type, figure, description=""):
        """Save user-modified plot for future use."""
        try:
            if not hasattr(self.parent, 'plot_cache'):
                self.parent.plot_cache = {}
            
            self.parent.plot_cache[plot_type] = {
                'figure': figure,
                'description': description,
                'timestamp': datetime.now(),
                'name': plot_type.replace('_', ' ').title()
            }
        except Exception as e:
            print(f"Error saving user plot: {e}")

    def _create_plot_selection_dialog(self):
        """Create modern dialog for plot selection with fixed checkmarks."""
        
        dialog = QDialog(self.parent if hasattr(self, 'parent') else self)
        dialog.setWindowTitle("Generate Report - Select Plots")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # FIX 1: Increased width to 850 to prevents text cutoff
        dialog.setFixedSize(850, 800)
        
        # Base64 encoded white checkmark icon
        check_icon = "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAADkSURBVDjLtZPBSgMxEEVt86ygBQ8e/EC96EVE8O/8AX/A0r/wY3wQDx78iSIqzMKC7IXiZmctM52Wwu6CJNm8d2cScB4W10c49i5+fF8h/xsC2u0Du38C+82y+6LVAw4Ab7OZR73/pP8D1EzjBqMctYtT2yJ3gIvn46Wz8zMHyCLdZPAyp6iW5e4AfrM9amFlVe/O0aXV1sB+s+y+ALWIVmmq5LvvFjQHz0cfrmyH3KPdGziE9xMQB2TV5O6F02d0EibXJ6ch4szl4sB6dSBv5uXCCFjIXyy7L1o94ADwNpt5/ALWN28zHQpFAAAAAElFTkSuQmCC)"

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: #2C3E50;
            }}
            QLabel#title {{
                font-size: 20px;
                font-weight: bold;
                color: #ECF0F1;
                padding: 20px 20px 10px 20px;
            }}
            QLabel#subtitle {{
                font-size: 13px;
                color: #BDC3C7;
                padding: 0px 20px 15px 20px;
            }}
            QLabel#sectionHeader {{
                font-size: 15px;
                font-weight: bold;
                color: #3498DB;
                padding: 15px 5px 5px 5px;
                border-bottom: 1px solid #34495E;
            }}
            
            /* CHECKBOX STYLING */
            QCheckBox {{
                font-size: 14px;
                color: #ECF0F1;
                padding: 8px;
                spacing: 12px;
                min-width: 400px; /* FIX 2: Force width to prevent text cutoff */
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border: 2px solid #5D6D7E;
                border-radius: 4px;
                background: #34495E;
            }}
            QCheckBox::indicator:checked {{
                background-color: #3498DB;
                border-color: #3498DB;
                /* FIX 3: Added the Base64 image here */
                image: {check_icon};
            }}
            QCheckBox::indicator:hover {{
                border-color: #3498DB;
            }}

            /* BUTTON STYLING */
            QPushButton {{
                background-color: #2980B9;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #3498DB;
            }}
            QPushButton#secondary {{
                background-color: transparent;
                border: 2px solid #2980B9;
                color: #3498DB;
            }}
            QPushButton#secondary:hover {{
                background-color: #2980B9;
                color: white;
            }}
            
            /* SCROLLBAR & FRAMES */
            QScrollBar:vertical {{
                border: none;
                background: #2C3E50;
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #5D6D7E;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QFrame#separator {{
                background-color: #34495E;
                margin: 0px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Header ---
        title = QLabel("Generate Comprehensive Report")
        title.setObjectName("title")
        main_layout.addWidget(title)
        
        subtitle = QLabel("Select the plots and visualizations to include in your PDF report.")
        subtitle.setObjectName("subtitle")
        main_layout.addWidget(subtitle)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)
        
        # --- Scroll Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;") # Ensure transparency
        
        scroll_widget = QWidget()
        scroll_widget.setObjectName("scrollContent")
        scroll_widget.setStyleSheet("background: transparent;") # Ensure transparency
        
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)
        scroll_layout.setContentsMargins(30, 10, 30, 10)
        
        checkboxes = {}
        
        # 1. Custom Plots Section
        special_section = QLabel("Current & Custom Plots")
        special_section.setObjectName("sectionHeader")
        scroll_layout.addWidget(special_section)
        
        current_cb = QCheckBox("Current Displayed Plot (with modifications)")
        current_cb.setChecked(True)
        scroll_layout.addWidget(current_cb)
        checkboxes['current_plot'] = current_cb
        
        parent_obj = self.parent if hasattr(self, 'parent') else self
        if hasattr(parent_obj, 'custom_plots') or hasattr(parent_obj, 'saved_figures'):
            custom_cb = QCheckBox("All Custom/Saved Plots")
            custom_cb.setChecked(True)
            scroll_layout.addWidget(custom_cb)
            checkboxes['custom_plots'] = custom_cb
        
        # 2. Standard Plots Section
        scroll_layout.addSpacing(15)
        standard_section = QLabel("Standard Analysis Plots")
        standard_section.setObjectName("sectionHeader")
        scroll_layout.addWidget(standard_section)
        
        plot_types = [
            ("Wind Rose", "wind_rose"),
            ("Wind Speed Distribution", "wind_speed_distribution"),
            ("Turbulence Intensity", "turbulence_intensity"),
            ("Wind Frequency Histogram", "wind_frequency_histogram"),
            ("Power Curve", "power_curve"),
            ("Actual Power Curve", "actual_power_curve"),
            ("Binned Power Curve", "binned_power_curve"),
            ("Rotor Speed Analysis", "rotor_speed_graph"),
            ("Power vs Generator Temp", "power_vs_generator_temperature"),
            ("Rotor Speed vs Gearbox Temp", "rotor_speed_vs_gearbox_temperature"),
            ("Ambient vs Nacelle Temp", "ambient_vs_nacelle_temperature"),
            ("Rotor Speed vs Gen Speed", "rotor_speed_vs_generator_speed"),
            ("Joint Distribution", "joint_distribution")
        ]
        
        for plot_name, plot_type in plot_types:
            cb = QCheckBox(plot_name)
            cb.setChecked(True)
            scroll_layout.addWidget(cb)
            checkboxes[plot_type] = cb
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)
        
        # --- Footer Buttons ---
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        main_layout.addWidget(sep2)
        
        button_frame = QFrame()
        button_frame.setStyleSheet("QFrame { background-color: #233140; }")
        button_frame.setFixedHeight(90)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.setObjectName("secondary")
        
        select_none_btn = QPushButton("Deselect All")
        select_none_btn.setObjectName("secondary")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        
        ok_btn = QPushButton("Generate Report")
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_none_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        button_frame.setLayout(button_layout)
        main_layout.addWidget(button_frame)
        
        dialog.setLayout(main_layout)
        
        # Connect signals
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes.values()])
        select_none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes.values()])
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            return {plot_type: cb.isChecked() for plot_type, cb in checkboxes.items()}
        else:
            return None


# Usage in your main class:
def generate_report(self):
    """Enhanced report generation method for the main class."""
    generator = EnhancedReportGenerator(self)
    generator.generate_report()