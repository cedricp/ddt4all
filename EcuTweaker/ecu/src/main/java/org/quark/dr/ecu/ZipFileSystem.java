package org.quark.dr.ecu;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;
import java.util.zip.DataFormatException;
import java.util.zip.Inflater;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/*
 *
 * A simple class that fast extracts a file stored in a big (dense) zip file
 * I build an index that contains the position and zip information
 * in a hash map.
 * I can now unzip a file stored in a big zip file at the speed of light !
 * /!\ This class handles text files only
 *
 */

public class ZipFileSystem {
    static class CustomZipEntry{
        public long compressedSize, pos, uncompressedSize;
    }
    private HashMap<String, CustomZipEntry> m_directoryEntries;
    private final String m_zipFilePath;
    private final String m_indexFile;

    public ZipFileSystem(String zipFilePath, String applicationDirectory){
        m_directoryEntries = new HashMap<>();
        m_zipFilePath = zipFilePath;
        m_indexFile = applicationDirectory + "/ecu.idx";
    }

    public boolean importZipEntries(){
        try {
            JSONArray mainJson = new JSONArray(readFile(m_indexFile));
            for (int i = 0; i < mainJson.length(); ++i){
                JSONObject zipEntryJson = mainJson.getJSONObject(i);
                CustomZipEntry ze = new CustomZipEntry();
                ze.pos = zipEntryJson.getLong("pos");
                ze.compressedSize = zipEntryJson.getLong("compsize");
                ze.uncompressedSize = zipEntryJson.getLong("realsize");
                m_directoryEntries.put(zipEntryJson.getString("name"), ze);
            }
            return true;
        } catch (Exception e) {
            e.printStackTrace();
        }

        return false;
    }

    public void exportZipEntries(){
        Iterator zeit = m_directoryEntries.entrySet().iterator();
        JSONArray mainJson =  new JSONArray();
        while(zeit.hasNext()){
            HashMap.Entry pair = (HashMap.Entry)zeit.next();
            JSONObject jsonEntry = new JSONObject();
            try {
                jsonEntry.put("pos", ((CustomZipEntry) pair.getValue()).pos);
                jsonEntry.put("realsize", ((CustomZipEntry) pair.getValue()).uncompressedSize);
                jsonEntry.put("compsize", ((CustomZipEntry) pair.getValue()).compressedSize);
                jsonEntry.put("name", ((String)pair.getKey()));
                mainJson.put(jsonEntry);
            } catch (Exception e) {
                e.printStackTrace();
                return;
            }
        }

        try {
            FileWriter fileWriter = new FileWriter(m_indexFile);
            fileWriter.write(mainJson.toString(0));
            fileWriter.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /*
     * Map zip entries to fast load them
     * This is the slowest part
     */
    public void getZipEntries() {
        m_directoryEntries = new HashMap<>();
        try {
            FileInputStream zip_is = new FileInputStream(m_zipFilePath);
            ZipInputStream zis = new ZipInputStream(zip_is);
            ZipEntry ze;
            long pos = 0;
            while ((ze = zis.getNextEntry()) != null) {
                if(ze.isDirectory())
                    continue;
                String filename = ze.getName();
                long offset = 30 + ze.getName().length() + (ze.getExtra() != null ? ze.getExtra().length : 0);
                pos += offset;
                CustomZipEntry cze = new CustomZipEntry();
                cze.pos = pos;
                cze.compressedSize = ze.getCompressedSize();
                cze.uncompressedSize = ze.getSize();
                m_directoryEntries.put(filename, cze);
                pos += cze.compressedSize;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public boolean fileExists(String filename){
        return m_directoryEntries.containsKey(filename);
    }

    public String getZipFile(String filename) {
        byte[] array = getZipFileAsBytes(filename);
        try {
            return new String(array, 0, array.length, "UTF-8");
        } catch (Exception e){
            return "";
        }
    }

    public byte[] getZipFileAsBytes(String filename) {
        try {
            long pos = m_directoryEntries.get(filename).pos;
            long compressedSize = m_directoryEntries.get(filename).compressedSize;
            long realSize = m_directoryEntries.get(filename).uncompressedSize;
            byte[] array = new byte[(int)compressedSize];
            FileInputStream zip_is = new FileInputStream(m_zipFilePath);
            zip_is.getChannel().position(pos);
            zip_is.read(array, 0, (int)compressedSize);
            Inflater inflater = new Inflater(true);
            inflater.setInput(array, 0, (int)compressedSize);
            byte[] result = new byte[(int)realSize];
            inflater.inflate(result);
            inflater.end();
            return result;
        } catch(IOException e) {
            e.printStackTrace();
            return null;
        } catch (DataFormatException e){
            e.printStackTrace();
        }
        return null;
    }

    private String readFile(String file) throws IOException {
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            StringBuilder stringBuilder = new StringBuilder();
            String ls = System.getProperty("line.separator");
            while ((line = reader.readLine()) != null) {
                stringBuilder.append(line);
                stringBuilder.append(ls);
            }

            return stringBuilder.toString();
        }
    }
}
