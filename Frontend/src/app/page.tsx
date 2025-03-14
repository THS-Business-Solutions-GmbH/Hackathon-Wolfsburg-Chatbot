"use client"
import {useState} from "react";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import axios from "axios";
import OpenStreetMap from "@/components/OpenStreetMap";
import remarkGfm from "remark-gfm";

export default function Home() {
    const languages = [
        {code: "de", name: "Deutsch", flag: "de.svg"},
        {code: "en", name: "English", flag: "en.svg"},
        {code: "fr", name: "Français", flag: "fr.svg"},
        {code: "es", name: "Español", flag: "es.svg"},
        {code: "it", name: "Italiano", flag: "it.svg"},
    ];

    const [iframeSrc, setIframeSrc] = useState("https://ths-bs.de");
    const [selectedLang, setSelectedLang] = useState(languages[0]);
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [loadingNotes, setLoadingNotes] = useState(false);
    const [preview, setPreview] = useState(false);

    const [activeTab, setActiveTab] = useState(1);
    const [textInput, setTextInput] = useState("");


    const sendMessage = async () => {
        if (messages.length < 0) return;

        const userMessage = {
            role: "user",
            content: input
        };
        setMessages([...messages, userMessage]);
        setInput("");
        setLoading(true);

        try {

            const response = await axios.post("http://127.0.0.1:5000/", {language: selectedLang.name, text: input}, {
                headers: {"Content-Type": "application/json"},
            });

            const aiMessage = {role: "ai", content: response.data.content || "No response from AI"};
            if (response.data.hasOwnProperty("href")) {
                setIframeSrc(response.data.href)
            }
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error("Error:", error);
            setMessages((prev) => [...prev, {role: "ai", content: "Error processing request"}]);
        } finally {
            setLoading(false);
        }
    };

    const createNotes = async () => {
        const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
        if (lastMessage == null || lastMessage.role == "user") return;
        setLoadingNotes(true)

        try {

            const response = await axios.post("http://127.0.0.1:5000/summarize_notes", {
                language: selectedLang.name,
                history: lastMessage.content
            }, {
                headers: {"Content-Type": "application/json"},
            });

            setTextInput(response.data || "No response from AI")
        } catch (error) {
            console.error("Error:", error);
            setTextInput((prev) => "Error processing request");
        } finally {
            setLoadingNotes(false);
        }
    };


    return (
        <div className="px-2 h-screen">
            <div className="h-16">
                <div className="base-layout ">
                    <div className="layout-header flex justify-between items-center py-4">
                        <div className="left-header-layout flex items-center space-x-4">
                            <div className="left-header-items">
                                <Image src="/wolfsburg-logo.svg" alt="Logo" width={60} height={60}/>
                            </div>
                            <h1 className="text-4xl font-bold text-green-900">Wolfsbot</h1>
                        </div>

                        <div className="flex items-center space-x-4 border border-gray-300 px-4 py-2 rounded-lg shadow-md bg-white">
                            {languages.map((lang) => (
                                <button
                                    key={lang.code}
                                    onClick={() => setSelectedLang(lang)}
                                    className={`flex items-center pointer-events-auto px-3 py-2 rounded-md transition ${
                                        selectedLang.code === lang.code ? "bg-green-200" : "hover:bg-gray-100"
                                    }`}
                                >
                                    <Image src={lang.flag} alt={lang.name} width={24} height={24} className="mr-2"/>
                                    {lang.name}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="pt-17">
                    <div className="flex flex-col items-center w-full h-screen">
                        {/* Tabs */}
                        <div className="flex  space-x-4 w-full max-w-4xl pt-2 px-2 ">
                            {["Aktuelle Seite", "Open Street Map", "Notizen"].map((tab, index) => (
                                <button
                                    key={index}
                                    onClick={() => setActiveTab(index + 1)}
                                    className={`px-4 min-h-11 py-2 rounded-t-lg  border-x border-t border-gray-300 ${activeTab === index + 1
                                        ? "bg-gray-300 font-bold"
                                        : "bg-white  hover:bg-gray-200"
                                    }`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>
                        {/* Tab Content */}
                        <div
                            className="flex justify-center items-center w-full h-full rounded-lg bg-white p-4 border border-gray-300 max-w-4xl">
                            {activeTab === 1 ? (
                                <iframe
                                    src={iframeSrc}
                                    className="w-full h-full max-w-4xl "
                                    allowFullScreen
                                ></iframe>
                            ) : activeTab === 2 ? (
                                <OpenStreetMap/>
                            ) : activeTab === 3 ? (
                                <div className="w-full">
                                    <div className="grid grid-cols-2 gap-4">
                                        <button onClick={createNotes}
                                                className="bg-green-500 text-white px-6 py-3 rounded-lg"
                                                disabled={loading || loadingNotes}>
                                            {loadingNotes ? "Wolfsbot resümierend..." : loading ? "Wolfsbot denkt..." : "Zusammenfassung erstellen"}
                                        </button>
                                        <button className="bg-green-500 text-white space-x-2 px-6 py-3 rounded-lg"
                                                onClick={() => setPreview(!preview)}>
                                            {preview ? "Editieren" : "Vorschau"}
                                        </button>
                                    </div>
                                    <div className="p-4">
                                        {preview ? (
                                            <div
                                                className="w-full p-3 border border-gray-300 rounded-lg bg-white min-h-[150px]">
                                                <ReactMarkdown>{textInput}</ReactMarkdown>
                                            </div>
                                        ) : (
                                            <textarea
                                                className="w-full h-150 p-3 border border-gray-300 rounded-lg resize-none"
                                                placeholder="Bitte geben Sie Ihre Notizen hier ein"
                                                value={textInput}
                                                onChange={(e) => setTextInput(e.target.value)}
                                            />
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <p className="text-gray-500">Loading...</p>
                            )}
                        </div>
                    </div>

                </div>
                <div className="pt-30">
                    <div
                        className="flex flex-col w-full max-w-3xl mx-auto bg-white h-[80vh] max-h-[600px] border border-gray-300 rounded-lg">
                        <div className="flex-1 overflow-y-auto space-y-2 p-4">
                            {messages.map((msg, i) => (
                                <div key={i}
                                     className={`p-3 rounded-lg max-w-lg ${msg.role === "user" ? "bg-green-500 text-white self-end ml-auto" : "bg-gray-300 text-black self-start"}`}>
                                    {msg.role === "ai" ? (

                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            ))}
                            {loading && <div className="text-gray-500">Der kluge Wolf überlegt... Es dauert nicht lange!
                                ⏳🐺</div>}
                        </div>

                        {/* Chat Input */}
                        <div className="flex gap-2 p-4 border-t border-gray-300">
                            <input
                                className="flex-1 p-3 border rounded-lg"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Wolfsbot steht bereit"
                                disabled={loading}
                                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                            />
                            <button onClick={sendMessage} className="bg-green-500 text-white px-6 py-3 rounded-lg"
                                    disabled={loading || loadingNotes}>
                                {loadingNotes ? "Wolfsbot resümierend..." : loading ? "Wolfsbot denkt..." : "Senden"}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
