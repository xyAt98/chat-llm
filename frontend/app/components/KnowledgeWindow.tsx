
"use client";

import { Heading, Flex, IconButton, useDisclosure, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, Button, Input, VStack, HStack, Text, useToast } from "@chakra-ui/react";
import { AddIcon } from "@chakra-ui/icons";
import { useState, useEffect } from "react";

export function KnowledgeWindow(props:{conversationId: string; shouldOpenModal?: boolean}){
    const { isOpen, onOpen, onClose } = useDisclosure();
    const [url, setUrl] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const toast = useToast();

    const handleAddKnowledge = () => {
        setUrl("");
        onOpen();
    };

    useEffect(() => {
        if (props.shouldOpenModal) {
            setUrl("");
            onOpen();
        }
    }, [props.shouldOpenModal]);

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
            const response = await fetch("http://localhost:8080/knowledge/url", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({'url': url}),
            });

            const data = await response.json();
            if (data.code === 200) {
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
            </div>

            <Modal isOpen={isOpen} onClose={onClose}>
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>添加来源</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody pb={6}>
                        <VStack spacing={4}>
                            <Text color="gray.600">
                                请输入要添加的网址URL：
                            </Text>
                            <Input
                                placeholder="https://example.com"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                // onKeyPress={(e) => {
                                //     if (e.key === "Enter") {
                                //         handleSubmit();
                                //     }
                                // }}
                            />
                            <HStack width="100%" justify="flex-end" spacing={3}>
                                <Button variant="outline" onClick={onClose}>
                                    取消
                                </Button>
                                <Button
                                    colorScheme="blue"
                                    onClick={handleSubmit}
                                    isLoading={isLoading}
                                >
                                    确认添加
                                </Button>
                            </HStack>
                        </VStack>
                    </ModalBody>
                </ModalContent>
            </Modal>
        </>
    );
}