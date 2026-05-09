import glob
import json
import locale

import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

import ddt4all.core.ecu.ecu_database as ecudb
import ddt4all.core.elm.elm as elm
import ddt4all.options as options
from ddt4all.ui.main_window.icons_paths import ICON_SCAN

_ = options.translator('ddt4all')

# Optional WebEngine import for enhanced features
try:
    import PyQt5.QtWebEngineWidgets as webkitwidgets
    HAS_WEBENGINE = True
except ImportError:
    print(_("Warning: PyQtWebEngine not available. Some features may be limited."))
    webkitwidgets = None
    HAS_WEBENGINE = False


class EcuList(widgets.QWidget):
    def __init__(self, ecuscan, treeview_ecu, vehicles):
        super(EcuList, self).__init__()
        self.selected = ''
        self.treeview_ecu = treeview_ecu
        self.vehicle_combo = widgets.QComboBox()
        self.ecuscan = ecuscan  # Store reference to ecuscan
        self.ecu_map = {}
        self.vehicles = vehicles
        self.populateVehicleCombo()

        self.vehicle_combo.activated.connect(self.filterProject)

        layout = widgets.QVBoxLayout()
        layouth = widgets.QHBoxLayout()
        scanbutton = widgets.QPushButton()
        scanbutton.setIcon(gui.QIcon(ICON_SCAN))
        scanbutton.clicked.connect(self.scanselvehicle)
        layouth.addWidget(self.vehicle_combo)
        layouth.addWidget(scanbutton)
        layout.addLayout(layouth)
        self.setLayout(layout)
        self.list = widgets.QTreeWidget(self)
        self.list.setSelectionMode(widgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list)
        self.ecuscan = ecuscan  # Store reference to ecuscan
        self.list.doubleClicked.connect(self.ecuSel)
        self.init()

    def populateVehicleCombo(self):
        """Populate vehicle combo box based on current sorting mode"""
        self.vehicle_combo.clear()
        
        # Check if vehicles database is available AND has ECUs
        if not self.vehicles or not self.vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            # No database available - add placeholder item
            self.vehicle_combo.addItem(_("No vehicles available"))
            self.vehicle_combo.setEnabled(False)
            return
        
        # Get current sorting mode from configuration
        sort_mode = options.get_carlist_sort_mode()
        
        if sort_mode == "name":
            # Sort by car name (extract from project key)
            vehicle_items = []
            for project_key in self.vehicles["projects"].keys():
                if project_key == "All":
                    # Keep "All" as is
                    display_name = "All"
                else:
                    # Extract car name from project key
                    # Format: [CODE] - Car Name -> Display: Car Name - [CODE]
                    if " - " in project_key:
                        parts = project_key.split(" - ", 1)
                        code_part = parts[0]  # [CODE]
                        name_part = parts[1]  # Car Name
                        display_name = f"{name_part} - {code_part}"
                    else:
                        display_name = project_key
                
                vehicle_items.append((display_name, project_key))
            
            # Sort by display name
            vehicle_items.sort(key=lambda x: x[0])
            
            # Add to combo box
            for display_name, project_key in vehicle_items:
                self.vehicle_combo.addItem(display_name, project_key)
        else:
            # Sort by project code (default behavior)
            for k in sorted(self.vehicles["projects"].keys()):
                self.vehicle_combo.addItem(k, k)
        
        # Enable combo box only if we have vehicles
        self.vehicle_combo.setEnabled(True)

    def refreshVehicleList(self):
        """Refresh the vehicle combo box when sorting mode changes"""
        current_selection = self.vehicle_combo.currentText()
        current_data = self.vehicle_combo.currentData()
        
        self.populateVehicleCombo()
        
        # Try to restore previous selection
        if current_data:
            index = self.vehicle_combo.findData(current_data)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)
        elif current_selection:
            index = self.vehicle_combo.findText(current_selection)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)

    def scanselvehicle(self):
        # Check if vehicles database is available AND has ECUs
        if not self.vehicles or not self.vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            return  # No database available, do nothing
        
        # Get project key (works for both sorting modes)
        project_key = self.vehicle_combo.currentData()
        if project_key is None:
            # Fallback to current text for backward compatibility
            project_key = self.vehicle_combo.currentText()
        
        # Skip if it's placeholder message
        if project_key == _("No vehicles available"):
            return
        
        project = str(self.vehicles["projects"][project_key]["code"])
        ecudb.addressing = self.vehicles["projects"][project_key]["addressing"]
        elm.snat = self.vehicles["projects"][project_key]["snat"]
        elm.snat_ext = self.vehicles["projects"][project_key]["snat_ext"]
        elm.dnat = self.vehicles["projects"][project_key]["dnat"]
        elm.dnat_ext = self.vehicles["projects"][project_key]["dnat_ext"]
        self.parent().parent().scan_project(project)

    def init(self):
        self.list.clear()
        self.list.setSortingEnabled(True)
        self.list.setColumnCount(8)
        self.list.model().setHeaderData(0, core.Qt.Horizontal, _('ECU name'))
        self.list.model().setHeaderData(1, core.Qt.Horizontal, _('ID'))
        self.list.model().setHeaderData(2, core.Qt.Horizontal, _('Protocol'))
        self.list.model().setHeaderData(3, core.Qt.Horizontal, _('Supplier'))
        self.list.model().setHeaderData(4, core.Qt.Horizontal, _('Diag'))
        self.list.model().setHeaderData(5, core.Qt.Horizontal, _('Soft'))
        self.list.model().setHeaderData(6, core.Qt.Horizontal, _('Version'))
        self.list.model().setHeaderData(7, core.Qt.Horizontal, _('Projets'))
        self.list.sortByColumn(0, core.Qt.AscendingOrder)
        stored_ecus = {"Custom": []}

        if self.ecuscan.getNumEcuDb() > 0:
            stored_ecus = {}

        custom_files = glob.glob("./json/*.json.targets")

        for cs in custom_files:
            f = open(cs, "r")
            jsoncontent = f.read()
            f.close()

            target = json.loads(jsoncontent)

            if not target:
                grp = "?"
                projects_list = []
                protocol = ''
            else:
                target = target[0]
                protocol = target['protocol']
                projects_list = target['projects']
                if target['address'] not in self.ecu_map:
                    grp = "?"
                else:
                    grp = self.ecu_map[target['address']]

            if grp not in stored_ecus:
                stored_ecus[grp] = []

            name = "/".join(projects_list)

            stored_ecus[grp].append([cs[:-8][7:], name, protocol])

        longgroupnames = {}
        for ecu in self.ecuscan.ecu_database.targets:
            if ecu.addr in self.ecuscan.ecu_database.addr_group_mapping:
                grp = self.ecuscan.ecu_database.addr_group_mapping[ecu.addr]
                if ecu.addr in self.ecuscan.ecu_database.addr_group_mapping_long:
                    longgroupnames[grp] = self.ecuscan.ecu_database.addr_group_mapping_long[ecu.addr]
            else:
                grp = "?"

            if grp not in stored_ecus:
                stored_ecus[grp] = []

            projname = "/".join(ecu.projects)

            soft = ecu.soft
            version = ecu.version
            supplier = ecu.supplier
            diag = ecu.diagversion

            row = [ecu.name, ecu.addr, ecu.protocol, supplier, diag, soft, version, projname]
            found = False
            for r in stored_ecus[grp]:
                if (r[0], r[1]) == (row[0], row[1]):
                    found = True
                    break
            if not found:
                stored_ecus[grp].append(row)

        keys = list(stored_ecus.keys())
        try:
            keys.sort(key=locale.strxfrm)
        except (locale.Error, AttributeError):
            keys.sort()
        for e in keys:
            item = widgets.QTreeWidgetItem(self.list, [e])
            if e in longgroupnames:
                item.setToolTip(0, longgroupnames[e])
            elif e in self.ecuscan.ecu_database.addr_group_mapping:
                item.setToolTip(0, self.ecuscan.ecu_database.addr_group_mapping[e])
            for t in stored_ecus[e]:
                widgets.QTreeWidgetItem(item, t)

        self.list.resizeColumnToContents(0)

    def filterProject(self):
        # Check if vehicles database is available AND has ECUs
        if not self.vehicles or not self.vehicles.get("projects") or self.ecuscan.getNumEcuDb() == 0:
            return  # No database available, do nothing
        
        # Get project key (works for both sorting modes)
        project_key = self.vehicle_combo.currentData()
        if project_key is None:
            # Fallback to current text for backward compatibility
            project_key = self.vehicle_combo.currentText()
        
        # Skip if it's placeholder message
        if project_key == _("No vehicles available"):
            return
        
        project = str(self.vehicles["projects"][project_key]["code"])
        ecudb.addressing = self.vehicles["projects"][project_key]["addressing"]
        elm.snat = self.vehicles["projects"][project_key]["snat"]
        elm.snat_ext = self.vehicles["projects"][project_key]["snat_ext"]
        elm.dnat = self.vehicles["projects"][project_key]["dnat"]
        elm.dnat_ext = self.vehicles["projects"][project_key]["dnat_ext"]

        root = self.list.invisibleRootItem()
        root_items = [root.child(i) for i in range(root.childCount())]

        for root_item in root_items:
            root_hidden = True

            items = [root_item.child(i) for i in range(root_item.childCount())]
            for item in items:
                if (project.upper() in str(item.text(7)).upper().split("/")) or project == "ALL":
                    item.setHidden(False)
                    root_hidden = False
                else:
                    item.setHidden(True)
            root_item.setHidden(root_hidden)

    def ecuSel(self, index):
        if index.parent() == core.QModelIndex():
            return
        item = self.list.model().itemData(self.list.model().index(index.row(), 0, index.parent()))

        selected = item[0]
        target = self.ecuscan.ecu_database.getTarget(selected)
        name = selected
        if target:
            self.ecuscan.addTarget(target)
            if target.addr in self.ecuscan.ecu_database.addr_group_mapping:
                group = self.ecuscan.ecu_database.addr_group_mapping[target.addr]
            else:
                group = "Unknown"
            name = "[ " + group + " ] " + name
        if selected:
            if name not in options.main_window.ecunamemap:
                options.main_window.ecunamemap[name] = selected
                self.treeview_ecu.addItem(name)
