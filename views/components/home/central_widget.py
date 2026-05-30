# from PyQt5.QtWidgets import *

# class CentralWidget(QWidget):
#     def __init__(self, parent=None, data_manager=None, data_table_module=None, 
#                  db_manager=None, project_id_getter=None):
#         super().__init__(parent)
#         self.data_manager = data_manager
#         self.data_table_module = data_table_module
#         self.db_manager = db_manager
#         self.project_id_getter = project_id_getter
#         self.map_widget = None
#         self.dashboard_widget = None
#         self.initUI()

#     def initUI(self):
#         self.main_layout = QVBoxLayout(self)
#         self.stack_widget = QStackedWidget()
#         self.main_layout.addWidget(self.stack_widget)

#         # Change: Default to dashboard instead of data table
#         self.show_dashboard() # initailize dashboard

#         # if self.data_table_module:
#         #     self.stack_widget.addWidget(self.data_table_module)
#         #     self.stack_widget.setCurrentWidget(self.data_table_module)

#     def toggle_view(self):
#         if self.stack_widget.currentWidget() == self.data_table_module:
#             self.show_map()
#         else:
#             self.show_table()
    
#     def show_map(self):
#         if not self.map_widget:
#             from controllers.turbine_map import TurbineMapController
#             map_ctrl = TurbineMapController(self.db_manager, self.project_id_getter())
#             self.map_widget = map_ctrl.get_map_widget()
#             self.stack_widget.addWidget(self.map_widget)
        
#         self.stack_widget.setCurrentWidget(self.map_widget)
    
#     # def show_table(self):
#     #     self.stack_widget.setCurrentWidget(self.data_table_module)
#     def show_table(self):
#         # Change: Make data table optional - create it lazily if not already added
#         if not self.data_table_module:
#             # If data_table_module wasn't provided, you might need to instantiate it here
#             # For now, assume it's passed in; if not, handle accordingly
#             pass
#         if self.data_table_module and self.data_table_module not in [self.stack_widget.widget(i) for i in range(self.stack_widget.count())]:
#             self.stack_widget.addWidget(self.data_table_module)
        
#         self.stack_widget.setCurrentWidget(self.data_table_module)

#     def update_data_table(self, data):
#         if self.data_table_module:
#             self.data_table_module.update_data_table(data)
#             self.show_table()

#     def show_placeholder(self):
#         self.stack_widget.setCurrentWidget(None)

#     # def show_dashboard(self):
#     #     if not hasattr(self, 'dashboard_widget'):
#     #         from views.dashboard.dashboard_widget import EngineeringDashboard
#     #         self.dashboard_widget = EngineeringDashboard(self.db_manager, self.project_id_getter())
#     #         self.stack_widget.addWidget(self.dashboard_widget)
        
#     #     self.stack_widget.setCurrentWidget(self.dashboard_widget)

#     # Add this method to CentralWidget class in central_widget.py

#     def show_dashboard(self):
#         if not hasattr(self, 'unified_dashboard_widget'):
#             from views.dashboard.dashboard_widget import UnifiedDashboard
#             self.unified_dashboard_widget = UnifiedDashboard(self.db_manager, self.project_id_getter())
#             self.stack_widget.addWidget(self.unified_dashboard_widget)
        
#         self.stack_widget.setCurrentWidget(self.unified_dashboard_widget)
    
#     def toggle_dashboard_table(self):
#         if self.stack_widget.currentWidget() == self.unified_dashboard_widget:
#             self.show_table()
#         else:
#             self.show_dashboard()

from PyQt5.QtWidgets import *

class CentralWidget(QWidget):
    def __init__(self, parent=None, data_manager=None, data_table_module=None, 
                 db_manager=None, project_id_getter=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.data_table_module = data_table_module
        self.db_manager = db_manager
        self.project_id_getter = project_id_getter
        self.map_widget = None
        self.unified_dashboard_widget = None  # Widget reference
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.stack_widget = QStackedWidget()
        self.main_layout.addWidget(self.stack_widget)

        # FIX: Show placeholder initially instead of immediately loading dashboard
        # This prevents data loading errors when project_id is not ready yet
        placeholder = QWidget()
        self.stack_widget.addWidget(placeholder)
        self.stack_widget.setCurrentWidget(placeholder)

    def toggle_view(self):
        if self.stack_widget.currentWidget() == self.data_table_module:
            self.show_map()
        else:
            self.show_table()
    
    def show_map(self):
        if not self.map_widget:
            from controllers.turbine_map import TurbineMapController
            map_ctrl = TurbineMapController(self.db_manager, self.project_id_getter())
            self.map_widget = map_ctrl.get_map_widget()
            self.stack_widget.addWidget(self.map_widget)
        
        self.stack_widget.setCurrentWidget(self.map_widget)
    
    def show_table(self):
        if not self.data_table_module:
            return
        if self.data_table_module not in [self.stack_widget.widget(i) for i in range(self.stack_widget.count())]:
            self.stack_widget.addWidget(self.data_table_module)
        
        self.stack_widget.setCurrentWidget(self.data_table_module)

    def update_data_table(self, data):
        if self.data_table_module:
            self.data_table_module.update_data_table(data)
            # After data is loaded, show dashboard (now data is available)
            self.show_dashboard()

    def show_placeholder(self):
        placeholder = QWidget()
        if placeholder not in [self.stack_widget.widget(i) for i in range(self.stack_widget.count())]:
            self.stack_widget.addWidget(placeholder)
        self.stack_widget.setCurrentWidget(placeholder)

    def show_dashboard(self):
        # FIX: Lazy-load dashboard only when actually requested
        # This way data is guaranteed to be available
        if not self.unified_dashboard_widget:
            try:
                from views.dashboard.dashboard_widget import UnifiedDashboard
                self.unified_dashboard_widget = UnifiedDashboard(self.db_manager, self.project_id_getter())
                self.stack_widget.addWidget(self.unified_dashboard_widget)
            except Exception as e:
                print(f"Error loading dashboard: {e}")
                self.show_placeholder()
                return
        
        self.stack_widget.setCurrentWidget(self.unified_dashboard_widget)
    
    def toggle_dashboard_table(self):
        if self.stack_widget.currentWidget() == self.unified_dashboard_widget:
            self.show_table()
        else:
            self.show_dashboard()

    def refresh_dashboard(self):
        """Destroy stale dashboard and rebuild with fresh data after replace."""
        if self.unified_dashboard_widget:
            self.stack_widget.removeWidget(self.unified_dashboard_widget)
            self.unified_dashboard_widget.deleteLater()
            self.unified_dashboard_widget = None
        self.show_dashboard()