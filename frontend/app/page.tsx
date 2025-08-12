"use client";

import { v4 as uuidv4 } from "uuid";
import { ChatWindow } from "./components/ChatWindow";
import { KnowledgeWindow } from "./components/KnowledgeWindow";
import { ToastContainer } from "react-toastify";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ChakraProvider } from "@chakra-ui/react";

export default function Home() {
  const pathname = usePathname();
  const [shouldOpenModal, setShouldOpenModal] = useState(false);

  const hasValidPathParameter = () => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const vectorIndex = urlParams.get('vector_index');
      return vectorIndex && vectorIndex.length > 0;
    }
    return false;
  };

  useEffect(() => {
    const hasValidParam = hasValidPathParameter();
    setShouldOpenModal(!hasValidParam);
  }, [pathname]);
  return (
    <ChakraProvider>
      <ToastContainer />
      <div className="flex flex-row items-center w-full h-full">
        <div className="w-1/5 h-full rounded-lg m-5" style={{ background: "rgb(36, 36, 37)"}}>
          <KnowledgeWindow conversationId={uuidv4()} shouldOpenModal={shouldOpenModal}></KnowledgeWindow>
        </div>
        <div className="w-4/5 h-full rounded-lg m-5" style={{ background: "rgb(36, 36, 37)"}}>
          <ChatWindow conversationId={uuidv4()} disabled={shouldOpenModal}></ChatWindow>
        </div>
      </div>
    </ChakraProvider>
  );
}
