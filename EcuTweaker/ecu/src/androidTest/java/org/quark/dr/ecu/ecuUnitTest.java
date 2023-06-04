package org.quark.dr.ecu;

import org.junit.Test;

import java.io.InputStream;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import static org.hamcrest.CoreMatchers.is;
import static org.junit.Assert.*;


/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
public class ecuUnitTest {
    @Test
    public void test_ecu_little_endian(){
        InputStream is = this.getClass().getClassLoader().getResourceAsStream("UCH_LE.json");
        Ecu ecu = new Ecu(is);
        HashMap<String, Object> hash = new HashMap<>();
        byte[] uchTest = Ecu.hexStringToByteArray("61112110010104001400000000DCE9");
        HashMap<String, String> hash2 = ecu.getRequestValues(uchTest, "Trame 11 : Etats des entrées", false);
        Iterator<String> it = hash2.keySet().iterator();
        for (;it.hasNext();){
            String key = it.next();
            System.out.println("??  " + key + " = " + hash2.get(key));
            hash2.put(key, hash2.get(key));
        }


        hash.put("Code APV", "001122334455");
        byte[] frame;
        frame = ecu.setRequestValues("ACCEDER AU MODE APRES-VENTE", hash);
        System.out.println("??  " + Ecu.byteArrayToHex(frame));
    }

    @Test
    public void test_ecu_little_endian2(){
        InputStream is = this.getClass().getClassLoader().getResourceAsStream("DDCR_-_BEB2_a_BEB4_-_v5.0.json");
        Ecu ecu = new Ecu(is);
        HashMap<String, Object> hash = new HashMap<>();
        byte[] uchTest = Ecu.hexStringToByteArray("61A100000000940C0000840CAC30F7FFA00F43000000000A00000000");
        HashMap<String, String> hash2 = ecu.getRequestValues(uchTest, "Frame 1 : parameters", false);
        Iterator<String> it = hash2.keySet().iterator();
        for (;it.hasNext();){
            String key = it.next();
            System.out.println("??  " + key + " = " + hash2.get(key));
            hash2.put(key, hash2.get(key));
        }

    }

//    @Test
//    public void test_ecu() {
//        assertTrue(getClass().getResource("test.json") == null);
//        InputStream is = this.getClass().getClassLoader().getResourceAsStream("test.json");
//
//        Ecu ecu = new Ecu(is);
//        // ECU Methods check
//        byte[] testbyte = new byte[] {0x00, -1, 10};
//        byte[] ucttest = new byte[] {0x61, 0x0A, 0x16, 0x32, 0x32, 0x02, 0x58, 0x00, (byte)0xB4, 0x3C,
//                0x3C, 0x1E, 0x3C, 0x0A, 0x0A, 0x0A, 0x0A, 0x01, 0x2C, 0x5C, 0x61, 0x67, (byte)0xB5, (byte)0xBB,
//                (byte)0xC1, 0X0A};
//        // 3B 0A 16 32 32 02 58 00 B4 3C 3C 1E 3C 0A 0A 0A 0A 01 2C 5C 61 67 B5 BB C1 0A
//        byte[] ucttest2 = new byte[26];
//
//        BigInteger bi = new BigInteger("FF", 16);
//        BigInteger bi2 = new BigInteger("11111110", 2);
//
//        assertThat(ecu.hex8ToSigned(125), is(125));
//        assertThat(ecu.hex8ToSigned(254), is(-2));
//        assertThat(ecu.hex16ToSigned(63000), is(-2536));
//        assertThat(ecu.hex16ToSigned(6000), is(6000));
//        assertThat(ecu.padLeft("FFFF", 8, "0"), is("0000FFFF"));
//        assertThat(ecu.hexStringToByteArray("00FF0A"), is(testbyte));
//        assertThat(ecu.integerToBinaryString(1, 8), is ("00000001"));
//        assertThat(ecu.integerToBinaryString(254, 8), is ("11111110"));
//
//        assertThat(bi.intValue(), is(255));
//        assertThat(bi2.intValue(), is(254));
//
//        HashMap<String, String> hash = ecu.getRequestValues(ucttest, "ReadDataByLocalIdentifier: misc timings and values", false);
//        HashMap<String, Object> hash2 = new HashMap<>();
//        HashMap<String, Object> hash3 = new HashMap<>();
//
//        Iterator<String> it = hash.keySet().iterator();
//        for (;it.hasNext();){
//            String key = it.next();
//            System.out.println(">>>>>>> " + key + " = " + hash.get(key));
//            hash2.put(key, hash.get(key));
//        }
//        System.out.println("3B 0A 16 32 32 02 58 00 B4 3C 3C 1E 3C 0A 0A 0A 0A 01 2C 5C 61 67 B5 BB C1 0A");
//
//        byte[] frame = ecu.setRequestValues("WriteDataByLocalIdentifier: misc timings and val.", hash2);
//        for(byte c : frame) {
//            System.out.format("%02X ", c);
//        }
//        System.out.println();
//        hash3.put("VIN Data", "VF1000000000000");
//        hash3.put("VIN CRC", "AA BB");
//        frame = ecu.setRequestValues("WriteDataByLocalIdentifier: VIN", hash3);
//        for(byte c : frame) {
//            System.out.format("%02X ", c);
//        }
//        System.out.println();
//    }
//
//    @Test
//    public void test_layout() {
//        assertTrue(getClass().getResource("test.json.layout") == null);
//        InputStream is = this.getClass().getClassLoader().getResourceAsStream("test.json.layout");
//
//        Layout layout = new Layout(is);
//    }
//
//    @Test
//    public void test_isotp() {
//
//    }
//
//    @Test
//    public void test_readDTC() {
//        InputStream is = this.getClass().getClassLoader().getResourceAsStream("acu.json");
//        Ecu ecu = new Ecu(is);
//        System.out.println("?? >> DTC TEST");
//        ecu.decodeDTC("ReadDTC", "5706903161900161901461900b61");
//    }
//
//    @Test
//    public void test_Ident(){
//        EcuDatabase db = new EcuDatabase();
//        EcuDatabase.EcuIdentifierNew idn = db.new EcuIdentifierNew();
//        idn.diag_version = "9";
//        idn.version = "F00A161";
//        idn.soft_version = "SW09.C.04-B031-11.2-F04-07";
//        idn.supplier = "B517";
//        idn.addr = 41;
//        try {
//            db.loadDatabase("/data/data/ecu.zip", "/data");
//        } catch (EcuDatabase.DatabaseException e){
//            e.printStackTrace();
//            return;
//        }
//        ArrayList<EcuDatabase.EcuInfo> infos = db.identifyNewEcu(idn);
//        for (EcuDatabase.EcuInfo info : infos)
//            System.out.println("?? " + info.ecuName + " " + info.exact_match);
////        EcuDatabase.EcuInfo  info = db.identifyOldEcu(122, "61 80 82 00 44 66 27 44 32 31 33 82 00 38 71 38 00 A7 75 00 56 05 02 01 00 00");
////        System.out.println("?? " + info.ecuName + " " + info.exact_match);
//    }
}