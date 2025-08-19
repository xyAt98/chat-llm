
"use client";

import { Heading, Flex, IconButton, useDisclosure, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, Button, Input, VStack, HStack, Text, useToast, Checkbox, Box, Tabs, TabList, TabPanels, Tab, TabPanel } from "@chakra-ui/react";
import { AddIcon } from "@chakra-ui/icons";
import { useState, useEffect } from "react";

export function KnowledgeWindow(props:{conversationId: string; shouldOpenModal?: boolean; sources?: string[]; vectorIndex?: string | null}){
    const { isOpen, onOpen, onClose } = useDisclosure();
    const [url, setUrl] = useState("");
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [titles, setTitles] = useState<{id: string; title: string; checked: boolean}[]>([]);
    const toast = useToast();

    // 初始化 titles 从 sources prop
    useEffect(() => {
        if (props.sources && props.sources.length > 0) {
            debugger
            const initialTitles = props.sources.map((source, index) => ({
                id: `source-${index}`,
                title: source,
                checked: true
            }));
            setTitles(initialTitles);
        }
    }, [props.sources]);

    const handleAddKnowledge = () => {
        setUrl("");
        setSelectedFile(null);
        onOpen();
    };

    useEffect(() => {
        if (props.shouldOpenModal) {
            setUrl("");
            setSelectedFile(null);
            onOpen();
        }
    }, [props.shouldOpenModal]);

    const handleFileUpload = async () => {
        if (!selectedFile) {
            toast({
                title: "请选择文件",
                status: "warning",
                duration: 2000,
            });
            return;
        }

        setIsLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            if (props.vectorIndex) {
                formData.append('index_name', props.vectorIndex);
            }

            const response = await fetch("http://localhost:8080/knowledge/file", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            if (data.code === 200) {
                const currentPageUrl = new URL(window.location.href);
                const hasVectorIndex = currentPageUrl.searchParams.has('vector_index');
                
                if (!hasVectorIndex && data.index_name) {
                    currentPageUrl.searchParams.set('vector_index', data.index_name);
                    const new_url = currentPageUrl.toString();
                    window.location.href = new_url;
                    return;
                }
                
                const newTitle = {
                    id: Date.now().toString(),
                    title: data.title || selectedFile.name,
                    checked: true
                };
                setTitles(prev => [...prev, newTitle]);
                toast({
                    title: "上传成功",
                    description: `已成功上传书籍: ${data.title}`,
                    status: "success",
                    duration: 2000,
                });
                onClose();
            } else {
                toast({
                    title: "上传失败",
                    description: data.error || "未知错误",
                    status: "error",
                    duration: 2000,
                });
            }
        } catch (error) {
            toast({
                title: "网络错误",
                description: "无法连接到服务器",
                status: "error",
                duration: 2000,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async () => {
        if (!url.trim()) {
            toast({
                title: "请输入URL",
                status: "warning",
                duration: 2000,
            });
            return;
        }

        setIsLoading(true);
        try {
            const requestBody: {url: string; index_name?: string} = {'url': url};
            
            // 如果有 vectorIndex 参数，添加到请求体中
            if (props.vectorIndex) {
                requestBody.index_name = props.vectorIndex;
            }
            debugger
            const response = await fetch("http://localhost:8080/knowledge/url", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();
            if (data.code === 200) {
                // 判断当前页面URL是否包含vector_index参数
                const currentPageUrl = new URL(window.location.href);
                const hasVectorIndex = currentPageUrl.searchParams.has('vector_index');
                
                if (!hasVectorIndex && data.index_name) {
                    // 如果没有vector_index参数，添加该参数并跳转
                    currentPageUrl.searchParams.set('vector_index', data.index_name);
                    const new_url = currentPageUrl.toString();
                    window.location.href = new_url;
                    return; // 跳转后不执行后续逻辑
                }
                
                const newTitle = {
                    id: Date.now().toString(),
                    title: data.title || url,
                    checked: true
                };
                setTitles(prev => [...prev, newTitle]);
                toast({
                    title: "添加成功",
                    description: `已成功添加知识: ${data.title}`,
                    status: "success",
                    duration: 2000,
                });
                onClose();
            } else {
                toast({
                    title: "添加失败",
                    description: data.error || "未知错误",
                    status: "error",
                    duration: 2000,
                });
            }
        } catch (error) {
            toast({
                title: "网络错误",
                description: "无法连接到服务器",
                status: "error",
                duration: 2000,
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <div className="flex flex-col items-center p-8 rounded grow max-h-full">
                <div className="w-full border-b border-gray-700 pb-4 mb-4">
                    <Flex justify="space-between" align="center" width="100%">
                        <Heading fontSize="xl" fontWeight="medium" color="white">
                            Knowledge Base
                        </Heading>
                        <IconButton
                            aria-label="Add knowledge"
                            icon={<AddIcon />}
                            colorScheme="blue"
                            size="sm"
                            rounded="full"
                            onClick={handleAddKnowledge}
                        />
                    </Flex>
                </div>
                
                {/* TitleGroup Component */}
                <VStack spacing={2} align="stretch" width="100%" maxH="60vh" overflowY="auto">
                    {titles.map((item) => (
                        <HStack key={item.id} p={2} borderRadius="md" _hover={{ bg: "gray.700" }}>
                            <Checkbox 
                                isChecked={item.checked}
                                onChange={(e) => {
                                    setTitles(prev => prev.map(t => 
                                        t.id === item.id ? { ...t, checked: e.target.checked } : t
                                    ));
                                }}
                                colorScheme="blue"
                            />
                            <Text 
                                color="white" 
                                fontSize="sm" 
                                flex={1}
                                noOfLines={1}
                                title={item.title}
                            >
                                {item.title}
                            </Text>
                        </HStack>
                    ))}
                    {titles.length === 0 && (
                        <Text color="gray.500" fontSize="sm" textAlign="center" py={4}>
                            暂无知识来源，点击 + 添加
                        </Text>
                    )}
                </VStack>
            </div>

            <Modal isOpen={isOpen} onClose={onClose} size="md">
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>添加知识来源</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody pb={6}>
                        <Tabs variant="soft-rounded" colorScheme="blue">
                            <TabList mb={4}>
                                <Tab>上传书籍</Tab>
                                <Tab>添加网址</Tab>
                            </TabList>
                            <TabPanels>
                                <TabPanel>
                                    <VStack spacing={4}>
                                        <Text color="gray.600">
                                            请选择要上传的书籍文件：
                                        </Text>
                                        <Input
                                            type="file"
                                            accept=".pdf,.epub,.txt,.doc,.docx"
                                            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                            p={1}
                                        />
                                        <Text fontSize="xs" color="gray.500">
                                            支持格式：PDF, EPUB, TXT, DOC, DOCX
                                        </Text>
                                        <HStack width="100%" justify="flex-end" spacing={3}>
                                            <Button variant="outline" onClick={onClose}>
                                                取消
                                            </Button>
                                            <Button
                                                colorScheme="blue"
                                                onClick={handleFileUpload}
                                                isLoading={isLoading}
                                                isDisabled={!selectedFile}
                                            >
                                                确认上传
                                            </Button>
                                        </HStack>
                                    </VStack>
                                </TabPanel>
                                <TabPanel>
                                    <VStack spacing={4}>
                                        <Text color="gray.600">
                                            请输入要添加的网址URL：
                                        </Text>
                                        <Input
                                            placeholder="https://example.com"
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                        />
                                        <HStack width="100%" justify="flex-end" spacing={3}>
                                            <Button variant="outline" onClick={onClose}>
                                                取消
                                            </Button>
                                            <Button
                                                colorScheme="blue"
                                                onClick={handleSubmit}
                                                isLoading={isLoading}
                                                isDisabled={!url.trim()}
                                            >
                                                确认添加
                                            </Button>
                                        </HStack>
                                    </VStack>
                                </TabPanel>
                            </TabPanels>
                        </Tabs>
                    </ModalBody>
                </ModalContent>
            </Modal>
        </>
    );
}