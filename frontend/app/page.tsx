"use client";

import { v4 as uuidv4 } from "uuid";
import { ChatWindow } from "./components/ChatWindow";
import { KnowledgeWindow } from "./components/KnowledgeWindow";
import { ToastContainer, toast } from "react-toastify";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ChakraProvider } from "@chakra-ui/react";
import { apiBaseUrl } from "./utils/constants";

export default function Home() {
  const pathname = usePathname();
  const [shouldOpenModal, setShouldOpenModal] = useState(false);
  const [sources, setSources] = useState<string[]>([]);
  const [vectorIndex, setVectorIndex] = useState<string | null>(null);

  const removeVectorIndexAndRedirect = () => {
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      const searchParams = url.searchParams;
      
      searchParams.delete('vector_index');
      
      url.search = searchParams.toString();
      
      setTimeout(() => {
        window.location.href = url.toString();
      }, 2000); // 2秒延迟
    }
  };

  const hasValidPathParameter = async () => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const vectorIndexParam = urlParams.get('vector_index');
      
      if (!vectorIndexParam || vectorIndexParam.length === 0) {
        return false;
      }
      
      // 设置 vectorIndex 状态
      setVectorIndex(vectorIndexParam);

      try {
        const response = await fetch(`${apiBaseUrl}/check_vector_store/${vectorIndexParam}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok || response.ok === undefined) {
          toast.error("向量数据库检查失败");
          removeVectorIndexAndRedirect();
        }

        const result = await response.json();
        
        if ((result && result.code !== 200) || !result) {
          toast.error("向量数据库不存在或无效");
          removeVectorIndexAndRedirect();
        }

        // 设置 sources 数据
        if (result && result.data && result.data.sources && Array.isArray(result.data.sources)) {
          setSources(result.data.sources);
        }

        return true;
      } catch (error) {
        toast.error("检查向量数据库时发生错误");
        removeVectorIndexAndRedirect();
      }
    }
    return false;
  };

  useEffect(() => {
    const checkPathParameter = async () => {
      const hasValidParam = await hasValidPathParameter();
      setShouldOpenModal(!hasValidParam);
    };
    
    checkPathParameter();
  }, [pathname]);
  return (
    <ChakraProvider>
      <ToastContainer />
      <div className="flex flex-row items-center w-full h-full">
        <div className="w-1/5 h-full rounded-lg m-5" style={{ background: "rgb(36, 36, 37)"}}>
          <KnowledgeWindow conversationId={uuidv4()} shouldOpenModal={shouldOpenModal} sources={sources} vectorIndex={vectorIndex}></KnowledgeWindow>
        </div>
        <div className="w-4/5 h-full rounded-lg m-5" style={{ background: "rgb(36, 36, 37)"}}>
          <ChatWindow conversationId={uuidv4()} disabled={shouldOpenModal}></ChatWindow>
        </div>
      </div>
    </ChakraProvider>
  );
}
