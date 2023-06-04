package org.quark.dr.ecu;

import android.os.Environment;
import androidx.annotation.Nullable;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

public class EcuDatabase {
    boolean m_loaded;
    private HashMap<Integer, ArrayList<EcuInfo>> m_ecuInfo;
    private HashMap<Integer, String> m_ecuAddressing;
    private Set<String> m_projectSet;
    private String m_ecuFilePath;
    private ZipFileSystem m_zipFileSystem;

    private HashMap<Integer, String> RXADDRMAP, TXADDRMAP;
    private HashMap<String, String> MODELSMAP;

    private static final String RXAT =
            "01: 760, 02: 724, 04: 762, 06: 791, 07: 771, 08: 778, 09: 7EB, 0D: 775," +
            "0E: 76E, 0F: 770, 11: 7C9, 13: 732, 16: 18DAF271, 1A: 731, 1B: 7AC, 1C: 76B," +
            "1E: 768, 23: 773, 24: 77D, 25: 700, 26: 765, 27: 76D, 28: 7D7, 29: 764," +
            "2A: 76F, 2B: 735, 2C: 772, 2D: 18DAF12D, 2E: 7BC, 2F: 76C, 32: 776, 3A: 7D2," +
            "40: 727, 41: 18DAF1D2, 46: 7CF, 47: 7A8, 4D: 7BD, 50: 738, 51: 763, 57: 767," +
            "58: 767, 59: 734, 5B: 7A5, 60: 18DAF160, 61: 7BA, 62: 7DD, 63: 73E, 64: 7D5," +
            "66: 739, 67: 793, 68: 77E, 6B: 7B5, 6E: 7E9, 73: 18DAF273, 77: 7DA, 78: 7BD," +
            "79: 7EA, 7A: 7E8, 7C: 77C, 81: 761, 82: 7AD, 86: 7A2, 87: 7A0, 91: 7ED," +
            "93: 7BB, 95: 7EC, 97: 7C8, A1: 76C, A5: 725, A6: 726, A7: 733, A8: 7B6," +
            "C0: 7B9, D0: 18DAF1D0, D1: 7EE, D2: 18DAF1D2, D3: 7EE, D6: 18DAF2D6, DA: 18DAF1DA," +
            "DB: 18DAF1DB, DE: 69C, DF: 18DAF1DF, E0: 18DAF1E0, E1: 18DAF1E1, E2: 18DAF1E2," +
            "E3: 18DAF1E3, E4: 757, E6: 484, E7: 7EC, E8: 5C4, E9: 762, EA: 4B3, EB: 5B8," +
            "EC: 5B7, ED: 704, F7: 736, F8: 737, FA: 77B, FD: 76F, FE: 76C, FF: 7D0";

    private static final String TXAT =
            "01: 740, 02: 704, 04: 742, 06: 790, 07: 751, 08: 758, 09: 7E3, 0D: 755," +
            "0E: 74E, 0F: 750, 11: 7C3, 13: 712, 15: 18DA15F1, 16: 18DA71F2, 18: 18DA18F1," +
            "1A: 711, 1B: 7A4, 1C: 74B, 1E: 748, 23: 753, 24: 75D, 25: 70C, 26: 745," +
            "27: 74D, 28: 78A, 29: 744, 2A: 74F, 2B: 723, 2C: 752, 2D: 18DA2DF1, 2E: 79C," +
            "2F: 74C, 32: 756, 3A: 7D6, 40: 707, 41: 18DAD0F1, 46: 7CD, 47: 788, 4D: 79D," +
            "50: 718, 51: 743, 57: 747, 58: 747, 59: 714, 5B: 785, 60: 18DA60F1, 61: 7B7," +
            "62: 7DC, 63: 73D, 64: 7D4, 66: 719, 67: 792, 68: 75A, 6B: 795, 6E: 7E1," +
            "73: 18DA73F2, 77: 7CA, 78: 746, 79: 7E2, 7A: 7E0, 7B: 18DA72F2, 7C: 75C," +
            "81: 73F, 82: 7AA, 86: 782, 87: 780, 91: 7E5, 93: 79B, 95: 7E4, 97: 7D8," +
            "A1: 74C, A5: 705, A6: 706, A7: 713, A8: 796, C0: 799, D0: 18DAD0F1, D1: 7E6," +
            "D2: 18DAD2F1, D3: 7E6, D6: 18DAD6F2, DA: 18DADAF1, DB: 18DADBF1, DE: 6BC," +
            "DF: 18DADFF1, E0: 18DAE0F1, E1: 18DAE1F1, E2: 18DAE2F1, E3: 18DAE3F1, E4: 74F," +
            "E6: 622, E7: 7E4, E8: 644, E9: 742, EA: 79A, EB: 638, EC: 637, ED: 714," +
            "F7: 716, F8: 717, FA: 75B, FD: 74F, FE: 74C, FF: 7D0";
    
    private static final String[] PROJECT_MODEL_DICT =
            {"XBA:KWID CN", "XBB:KWID BR", "X06:TWINGO", "X44:TWINGO II",
            "X07:TWINGO III", "X07PH2:TWINGO III Ph 2", "X77:MODUS", "X77PH2:MODUS Ph2", "X35:SYMBOL/THALIA", "XJC:SYMBOL/THALIA II",
            "X65:CLIO II",
            "X85:CLIO III", "X98:CLIO IV", "X98PH2:CLIO IV Ph 2", "XJA:CLIO V", "X87:CAPTUR", "X87PH2:CAPTUR Ph2", "XJB:CAPTUR II",
            "XJE:CAPTUR II CN", "X38:FLUENCE", "XFF:FLUENCE II", "X64:MEGANE/SCENIC I",
            "X84:MEGANE/SCENIC II", "X84PH2:MEGANE/SCENIC II Phase 2", "X95:MEGANE/SCENIC III", "X95PH2:MEGANE/SCENIC III Ph2",
            "XFB:MEGANE IV", "XFBPH2:MEGANE IV Ph2", "XFF:MEGANE IV SEDAN",
            "XFA:SCENIC IV","XFAPH2:SCENIC IV Ph 2",  "X56:LAGUNA", "X74:LAGUNA II",
            "X74PH2:LAGUNA II Phase 2", "X91:LAGUNA III","X91PH2:LAGUNA III Ph2", "X91PH3:LAGUNA III Ph3",
            "X47:LAGUNA III (tricorps)", "X66:ESPACE III", "X81:ESPACE IV", "X81PH2:ESPACE IV Ph2",
            "X81PH3:ESPACE IV Ph3", "X81PH4:ESPACE IV Ph4", "XFC:ESPACE V", "XFCPH2:ESPACE V Ph2",
            "X73:VELSATIS", "X73PH2:VELSATIS Ph2", "X43:LATITUDE", "XFD:TALISMAN", "XFDPH2:TALISMAN Ph 2", "H45:KOLEOS", "XZG:KOLEOS II",
            "XZGPH2:KOLEOS II Ph 2", "XZJ:KOLEOS II", "XZJPH2:KOLEOS II Ph2", "HFE:KADJAR",
            "HFEPH2:KADJAR Ph 2", "XZH:KADJAR CN", "XZHPH2:KADJAR Ph2 CN", "X33:WIND", "X09:TWIZY",
            "X10:ZOE", "X10PH2:ZOE Ph2", "X76:KANGOO I", "X61:KANGOO II", "X61PH2:KANGOO II Ph2", "XFK:KANGOO III",
            "X24:MASCOTT", "X83:TRAFFIC II", "X83PH2:TRAFFIC II Ph 2", "X82:TRAFFIC III", "X82PH2:TRAFFIC III Ph2",
            "X70:MASTER II","X70PH2:MASTER II Ph2","X70PH3:MASTER II Ph3",   "X62:MASTER III", "X62PH2:MASTER III Ph 2", "X90:LOGAN/SANDERO",
            "X52:LOGAN/SANDERO II", "X79:DUSTER", "X79PH2:DUSTER Ph2", "XJD:DUSTER II", "X67:DOKKER",
            "X92:LODGY", "XGA:BM LADA", "AS1:ALPINE", "X02:MICRA (NISSAN)", "X02E:MICRA (NISSAN)", "X21:NOTE (NISSAN)",
            "X21B:NOTE(B) (NISSAN)"
            };

    public class EcuIdent{
        public String supplier_code, soft_version, version, diagnostic_version;
    }

    public class EcuInfo {
        public Set<String> projects;
        public String href;
        public String ecuName, protocol;
        public int addressId;
        public EcuIdent ecuIdents[];
        public boolean exact_match;
    }

    public class DatabaseException extends Exception {
        public DatabaseException(String message) {
            super(message);
        }
    }

    public ArrayList<EcuInfo> getEcuInfo(int addr) {
        return m_ecuInfo.get(addr);
    }

    public ArrayList<String> getEcuByFunctions() {
        ArrayList<String> list = new ArrayList<>();
        Iterator<String> valueIterator = m_ecuAddressing.values().iterator();
        while (valueIterator.hasNext()) {
            list.add(valueIterator.next());
        }
        return list;
    }

    public class EcuIdentifierNew {
        public String supplier, version, soft_version, diag_version;
        public int addr;
        public EcuIdentifierNew() {
            reInit(-1);
        }
        public void reInit(int addr){
            this.addr = addr;
            supplier = version = soft_version = diag_version = "";
        }
        public boolean isFullyFilled(){
            return !supplier.isEmpty() && !version.isEmpty() && !soft_version.isEmpty() && !diag_version.isEmpty();
        }
    }

    @Nullable
    public EcuInfo identifyOldEcu(int addressId, String supplier, String soft_version, String version, int diag_version) {
        ArrayList<EcuInfo> ecuInfos = m_ecuInfo.get(addressId);
        if (ecuInfos == null)
            return null;
        EcuIdent closestEcuIdent = null;
        EcuInfo keptEcuInfo = null;
        for (EcuInfo ecuInfo : ecuInfos){
            for(EcuIdent ecuIdent: ecuInfo.ecuIdents) {
                if (ecuIdent.supplier_code.equals(supplier) && ecuIdent.soft_version.equals(soft_version)) {
                    if (ecuIdent.version.equals(version) && diag_version == Integer.parseInt(ecuIdent.diagnostic_version, 10)) {
                        ecuInfo.exact_match = true;
                        return ecuInfo;
                    }
                    if (closestEcuIdent == null){
                        closestEcuIdent = ecuIdent;
                        continue;
                    }
                    int intVersion = Integer.parseInt(version, 16);
                    int currentDiff = Math.abs(
                            Integer.parseInt(ecuIdent.version, 16) - intVersion);
                    int oldDiff = Math.abs(Integer.parseInt(
                            closestEcuIdent.version, 16) - intVersion);
                    if (currentDiff < oldDiff){
                        closestEcuIdent = ecuIdent;
                        keptEcuInfo = ecuInfo;
                    }
                }
            }
        }
        if (keptEcuInfo != null)
            keptEcuInfo.exact_match = false;
        return keptEcuInfo;
    }

    public ArrayList<EcuInfo> identifyNewEcu(EcuIdentifierNew ecuIdentifer){
        ArrayList<EcuInfo> ecuInfos = m_ecuInfo.get(ecuIdentifer.addr);
        ArrayList<EcuInfo> keptEcus= new ArrayList<>();
        for (EcuInfo ecuInfo : ecuInfos) {
            for (EcuIdent ecuIdent : ecuInfo.ecuIdents) {
                if (ecuIdent.supplier_code.equals(ecuIdentifer.supplier) &&
                        ecuIdent.version.equals(ecuIdentifer.version)) {
                    ecuInfo.exact_match = false;
                    keptEcus.add(ecuInfo);
                    if (ecuIdent.soft_version.equals(ecuIdentifer.soft_version)) {
                        ecuInfo.exact_match = true;
                        keptEcus.clear();
                        keptEcus.add(ecuInfo);
                        return keptEcus;
                    }
                }
            }
        }
        return keptEcus;
    }

    public ArrayList<String> getEcuByFunctionsAndType(String type) {
        Set<String> list = new HashSet<>();
        Iterator<ArrayList<EcuInfo>> ecuArrayIterator = m_ecuInfo.values().iterator();

        while (ecuArrayIterator.hasNext()) {
            ArrayList<EcuInfo> ecuArray = ecuArrayIterator.next();
            for (EcuInfo ecuInfo : ecuArray) {
                if ((ecuInfo.projects.contains(type) || type.isEmpty())
                        && m_ecuAddressing.containsKey(ecuInfo.addressId)) {
                    list.add(m_ecuAddressing.get(ecuInfo.addressId));
                }
            }
        }
        ArrayList<String> ret = new ArrayList<>();
        for (String txt : list) {
            ret.add(txt);
        }
        return ret;
    }

    public int getAddressByFunction(String name) {
        Set<Integer> keySet = m_ecuAddressing.keySet();
        for (Integer i : keySet) {
            if (m_ecuAddressing.get(i) == name) {
                return i;
            }
        }
        return -1;
    }

    public EcuDatabase() {
        m_loaded = false;
        m_ecuInfo = new HashMap<>();
        m_ecuAddressing = new HashMap<>();
        MODELSMAP = new HashMap<>();
        RXADDRMAP = new HashMap<>();
        TXADDRMAP = new HashMap<>();
        buildMaps();
        loadAddressing();
        loadModels();
    }

    public String[] getProjects(){
        return m_projectSet.toArray(new String[m_projectSet.size()]);
    }

    public String[] getModels() {
        return MODELSMAP.values().toArray(new String[MODELSMAP.size()]);
    }

    public String getProjectFromModel(String model){
        Iterator it = MODELSMAP.entrySet().iterator();
        while(it.hasNext()){
            Map.Entry keyval = (Map.Entry)it.next();
            if (((String)keyval.getValue()).toUpperCase().equals(model.toUpperCase())){
                return (String)keyval.getKey();
            }
        }
        return "";
    }

    private void loadModels(){
        for (int i = 0; i < PROJECT_MODEL_DICT.length; ++i){
            String[] split = PROJECT_MODEL_DICT[i].split(":");
            if (split.length != 2)
                continue;
            MODELSMAP.put(split[0], split[1]);
        }
        MODELSMAP.put("", "ALL");
    }

    private void filterProjects(){
        Iterator<String> its = m_projectSet.iterator();
        while(its.hasNext()) {
            Set<String> modelKeySet = MODELSMAP.keySet();
            String project = its.next();
            if (!MODELSMAP.containsKey(project)){
                MODELSMAP.remove(project);
            }
        }
    }
    
    public void checkMissings(){
        Iterator<String> its = m_projectSet.iterator();
        while(its.hasNext()){
            Set<String> modelKeySet = MODELSMAP.keySet();
            String project = its.next();
            if (!MODELSMAP.containsKey(project)){
                System.out.println("?? Missing " + project);
            }
        }
    }

    private void loadAddressing() {
        String addressingResource = "addressing.json";
        InputStream ecu_stream = getClass().getClassLoader().getResourceAsStream(addressingResource);
        String line;
        BufferedReader br;
        StringBuilder sb = new StringBuilder();

        try {
            br = new BufferedReader(new InputStreamReader(ecu_stream));
            while ((line = br.readLine()) != null) {
                sb.append(line + "\n");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        try {
            JSONObject jobj = new JSONObject(sb.toString());
            Iterator<String> keys = jobj.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                JSONArray ecuArray = jobj.getJSONArray(key);
                String name = ecuArray.getString(1);
                m_ecuAddressing.put(Integer.parseInt(key, 16), name);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public String loadDatabase(String ecuFilename, String appDir) throws DatabaseException {
        if (m_loaded) {
            Log.e("EcuDatabase", "Database already loaded");
            return m_ecuFilePath;
        }
        File checkEcuFile = new File(ecuFilename);
        if (!checkEcuFile.exists())
            ecuFilename = "";

        if (ecuFilename.isEmpty()) {
            ecuFilename = searchEcuFile(new File(Environment.getExternalStorageDirectory().getPath()));
        }
        if (ecuFilename.isEmpty()) {
            ecuFilename = searchEcuFile(new File(Environment.getDataDirectory().getPath()));
        }
        if (ecuFilename.isEmpty()) {
            ecuFilename = searchEcuFile(new File("/storage"));
        }
        if (ecuFilename.isEmpty()) {
            ecuFilename = searchEcuFile(new File("/mnt"));
        }
        if (ecuFilename.isEmpty()) {
            throw new DatabaseException("Ecu file (ecu.zip) not found");
        }

        String bytes;
        m_ecuFilePath = ecuFilename;
        String indexFileName = appDir + "/ecu.idx";

        File indexFile = new File(indexFileName);
        File ecuFile = new File(m_ecuFilePath);
        if (!ecuFile.exists()){
            throw new DatabaseException("Archive (ecu.zip) file not found");
        }
        long indexTimeStamp = indexFile.lastModified();
        long ecuTimeStamp = ecuFile.lastModified();
        m_zipFileSystem = new ZipFileSystem(m_ecuFilePath, appDir);

        /*
         * If index is already made, use it
         * Also check files exists and timestamps to force [re]scan
         */
        if (indexFile.exists() && (indexTimeStamp > ecuTimeStamp) && m_zipFileSystem.importZipEntries()){
            bytes = m_zipFileSystem.getZipFile("db.json");
            if (bytes.isEmpty()){
                throw new DatabaseException("Database (db.json) file not found");
            }
        } else {
            /*
             * Else create it
             */
            m_zipFileSystem.getZipEntries();
            m_zipFileSystem.exportZipEntries();
            bytes = m_zipFileSystem.getZipFile("db.json");
            if (bytes.isEmpty()){
                throw new DatabaseException("Database (db.json) file not found");
            }
        }

        JSONObject jsonRootObject;
        try {
            jsonRootObject = new JSONObject(bytes);
        } catch (Exception e) {
            throw new DatabaseException("JSON conversion issue");
        }

        m_projectSet = new HashSet<>();
        Set<Integer> addressSet = new HashSet<>();
        Iterator<String> keys = jsonRootObject.keys();
        for (; keys.hasNext(); ) {
            String href = keys.next();
            try {
                JSONObject ecuJsonObject = jsonRootObject.getJSONObject(href);
                JSONArray projectJsonObject = ecuJsonObject.getJSONArray("projects");
                Set<String> projectsSet = new HashSet<>();
                for (int i = 0; i < projectJsonObject.length(); ++i) {
                    String project = projectJsonObject.getString(i);
                    String upperCaseProject = project.toUpperCase();
                    projectsSet.add(upperCaseProject);
                    m_projectSet.add(upperCaseProject);
                }
                int addrId = Integer.parseInt(ecuJsonObject.getString("address"), 16);
                addressSet.add(addrId);
                EcuInfo info = new EcuInfo();
                info.ecuName = ecuJsonObject.getString("ecuname");
                info.href = href;
                info.projects = projectsSet;
                info.addressId = addrId;
                info.protocol = ecuJsonObject.getString("protocol");
                JSONArray jsAutoIdents = ecuJsonObject.getJSONArray("autoidents");
                info.ecuIdents = new EcuIdent[jsAutoIdents.length()];
                for (int i = 0; i < jsAutoIdents.length(); ++i) {
                    JSONObject jsAutoIdent = jsAutoIdents.getJSONObject(i);
                    info.ecuIdents[i] = new EcuIdent();
                    info.ecuIdents[i].soft_version = jsAutoIdent.getString("soft_version");
                    info.ecuIdents[i].supplier_code = jsAutoIdent.getString("supplier_code");
                    info.ecuIdents[i].version = jsAutoIdent.getString("version");
                    info.ecuIdents[i].diagnostic_version = jsAutoIdent.getString("diagnostic_version");
                }
                ArrayList<EcuInfo> ecuList;
                if (!m_ecuInfo.containsKey(addrId)) {
                    ecuList = new ArrayList<>();
                    m_ecuInfo.put(addrId, ecuList);
                } else {
                    ecuList = m_ecuInfo.get(addrId);
                }
                ecuList.add(info);
            } catch (Exception e) {
                e.printStackTrace();
                throw new DatabaseException("JSON parsing issue");
            }
        }

        Set<Integer> keySet = new HashSet<>(m_ecuAddressing.keySet());
        for (Integer key : keySet) {
            if (!addressSet.contains(key)) {
                m_ecuAddressing.remove(key);
            }
        }

        m_loaded = true;
        filterProjects();
        return ecuFilename;
    }

    public boolean isLoaded() {
        return m_loaded;
    }

    public String searchEcuFile(File dir) {
        if (!dir.exists()) {
            return "";
        }
        File listFile[] = dir.listFiles();
        if (listFile != null) {
            for (File f : listFile) {
                if (f.isDirectory()) {
                    String res = searchEcuFile(f);
                    if (!res.isEmpty())
                        return res;
                } else {
                    if (f.getName().equalsIgnoreCase("ecu.zip")) {
                        return f.getAbsolutePath();
                    }
                }
            }
        }
        return "";
    }

    public String getZipFile(String filePath){
        return m_zipFileSystem.getZipFile(filePath);
    }

    private void buildMaps(){
        String[] RXS = RXAT.replace(" ", "").split(",");
        String[] TXS = TXAT.replace(" ", "").split(",");

        for (String rxs : RXS){
            String[] idToAddr = rxs.split(":");
            RXADDRMAP.put(Integer.parseInt(idToAddr[0], 16), idToAddr[1]);
        }
        for (String txs : TXS){
            String[] idToAddr = txs.split(":");
            TXADDRMAP.put(Integer.parseInt(idToAddr[0], 16), idToAddr[1]);
        }
    }

    public String getRxAddressById(int id){
        return RXADDRMAP.get(id);
    }

    public String getTxAddressById(int id){
        return TXADDRMAP.get(id);
    }

    public ZipFileSystem getZipFileSystem(){
        return m_zipFileSystem;
    }
}
