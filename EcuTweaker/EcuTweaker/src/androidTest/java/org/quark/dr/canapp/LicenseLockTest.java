package org.quark.dr.canapp;

import org.junit.Test;

import java.text.DecimalFormat;

import static org.junit.Assert.*;
import static org.hamcrest.CoreMatchers.is;

public class LicenseLockTest {

//    @Test
//    public void test_armor(){
//        for (int i = 0; i < 0xFFFFFF; ++i){
//            String armored = LicenseLock.addArmor(Integer.toHexString(i).getBytes());
//            assertThat(Integer.toHexString(i), is(new String(LicenseLock.removeArmor(armored))));
//            LicenseLock lock = new LicenseLock(i);
//            String privateCode = lock.generatePrivateCode();
//            System.out.println("?? public " + lock.getPublicCode() + " private " + privateCode);
//            assertThat(lock.checkUnlock(privateCode), is(true));
//        }
//    }

    @Test
    public void test_Ident(){
        byte[] unarmor = LicenseLock.removeArmor("2jpgyt7gvb");
        String hexString = new String(unarmor);
        long id = Long.parseLong(hexString, 16);
        LicenseLock lock = new LicenseLock(id);
        System.out.println("?? Public " + lock.getPublicCode() + " " + hexString);
        System.out.println("?? Private " + lock.generatePrivateCode());
    }

}