"use client";

import { v4 as uuidv4 } from "uuid";
import { ChatWindow } from "./components/ChatWindow";
import { KnowledgeWindow } from "./components/KnowledgeWindow";
import { ToastContainer } from "react-toastify";

import { ChakraProvider } from "@chakra-ui/react";

export default function Home() {
  return (
    <ChakraProvider>
      <ToastContainer />
      <div className="flex flex-row items-center w-full h-full">
        <div className="w-1/5 h-full">
          <KnowledgeWindow conversationId={uuidv4()}></KnowledgeWindow>
        </div>
        <div className="w-4/5 h-full">
          <ChatWindow conversationId={uuidv4()}></ChatWindow>
        </div>
      </div>
    </ChakraProvider>
  );
}
