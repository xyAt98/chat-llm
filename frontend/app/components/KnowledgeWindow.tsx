
"use client";

import { Heading, Flex, IconButton } from "@chakra-ui/react";
import { AddIcon } from "@chakra-ui/icons";

export function KnowledgeWindow(props:{conversationId: string}){
    const handleAddKnowledge = () => {
        console.log('be clicked');
    };

    return (
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
    );
}