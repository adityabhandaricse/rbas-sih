import { createContext, useContext, useState, useCallback } from "react";

const LANG_MAP = { en: "en-IN", hi: "hi-IN", bn: "bn-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN" };

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState("en");

  const speak = useCallback((text) => {
    if (!("speechSynthesis" in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = LANG_MAP[language] || "en-IN";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }, [language]);

  const listen = useCallback((onResult) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input isn't supported in this browser.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = LANG_MAP[language] || "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => onResult(event.results[0][0].transcript);
    recognition.start();
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, speak, listen }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used inside LanguageProvider");
  return ctx;
}
