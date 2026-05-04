import { useState, useCallback } from "react";
import { generateKey, encryptFile } from "@/lib/crypto";

interface UseEncryptionReturn {
  key: CryptoKey | null;
  encryptedBlob: Blob | null;
  isEncrypting: boolean;
  error: string | null;
  encrypt: (file: File) => Promise<Blob | null>;
  clearKey: () => void;
}

export function useEncryption(): UseEncryptionReturn {
  const [key, setKey] = useState<CryptoKey | null>(null);
  const [encryptedBlob, setEncryptedBlob] = useState<Blob | null>(null);
  const [isEncrypting, setIsEncrypting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const encrypt = useCallback(async (file: File): Promise<Blob | null> => {
    setIsEncrypting(true);
    setError(null);
    try {
      const cryptoKey = await generateKey();
      setKey(cryptoKey);
      const blob = await encryptFile(file, cryptoKey);
      setEncryptedBlob(blob);
      return blob;
    } catch (e) {
      setError("Encryption failed");
      return null;
    } finally {
      setIsEncrypting(false);
    }
  }, []);

  const clearKey = useCallback(() => {
    setKey(null);
    setEncryptedBlob(null);
  }, []);

  return { key, encryptedBlob, isEncrypting, error, encrypt, clearKey };
}