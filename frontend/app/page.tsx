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
        <div className="w-1/5 h-full rounded-lg border-2 bg-blue-200 m-5">
          <KnowledgeWindow conversationId={uuidv4()}></KnowledgeWindow>
        </div>
        <div className="w-4/5 h-full rounded-lg border-2 bg-blue-200 m-5">
          <ChatWindow conversationId={uuidv4()}></ChatWindow>
        </div>
      </div>
    </ChakraProvider>
  );
}
