import { useState, useRef, useEffect } from 'react';
import { Box, VStack, Input, IconButton, Flex, Text, Avatar, Container, Button } from '@chakra-ui/react';
import { LuSearch } from 'react-icons/lu';
import { FaRegTrashAlt } from "react-icons/fa";
import AG2Client from '../AG2Client';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatWindowProps {
  onSendMessage: (message: string) => Promise<string>;
}

const defaultFirstMessage: Message = {
  id: Date.now().toString(),
  text: "Hello, I'm the lead finder chat bot. I'm here to help you find leads for your product. Please provide me with information about your company, the product you are selling, and information about your ideal customer profile.",
  sender: 'ai',
  timestamp: new Date(),
};

const ag2 = new AG2Client();

export const ChatWindow = ({ onSendMessage }: ChatWindowProps) => {
  const [messages, setMessages] = useState<Message[]>([defaultFirstMessage]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const aiResponseMessage = await onSendMessage(inputValue);
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: aiResponseMessage,
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewSession = async () => {
    console.log("handleNewSession");
    const res = await ag2.AG2_NewSession("new session");
    if (res === true) {
      window.location.reload();
    }
  };

  return (
    <Container maxW="container.md" h="80vh" py={4}>
      <Box
        h="full"
        borderWidth="1px"
        borderRadius="lg"
        overflow="hidden"
      >
        <VStack h="full" >
          {/* Messages Area */}
          <Box
            flex="1"
            w="full"
            overflowY="auto"
            p={4}
            css={{
              '&::-webkit-scrollbar': {
                width: '4px',
              },
              '&::-webkit-scrollbar-track': {
                width: '6px',
              },
              '&::-webkit-scrollbar-thumb': {
                borderRadius: '24px',
              },
            }}
          >
            <VStack align="stretch" >
              {messages.map((message) => (
                <Flex
                  key={message.id}
                  justify={message.sender === 'user' ? 'flex-end' : 'flex-start'}
                >
                    <Flex
                        maxW="70%"
                        gap={2}
                        direction={message.sender === 'user' ? 'row-reverse' : 'row'}
                     >
                        <Avatar.Root size="lg">
                            <Avatar.Fallback name={message.sender === 'user' ? 'User' : 'AI'} />
                            {(message.sender === 'ai') && <Avatar.Image src="https://platform.theverge.com/wp-content/uploads/sites/2/2025/02/openai-old-logo.png?quality=90&strip=all&crop=7.8125%2C0%2C84.375%2C100&w=2400" />}
                        </Avatar.Root>
                        <Box
                            bg={message.sender === 'user' ? 'blue.500' : 'green.500'}
                            color="white"
                            px={4}
                            py={2}
                            borderRadius="lg"
                            text-align={message.sender === 'user' ? 'right' : 'left'}
                        >
                            <Text>{message.text}</Text>
                        </Box>
                    </Flex>
                </Flex>
              ))}
              <div ref={messagesEndRef} />
            </VStack>
          </Box>

          {/* Input Area */}
          <Box
            w="full"
            p={4}
            borderTopWidth="1px"
          >
            <Flex gap={2}>
            <Button onClick={handleNewSession} bg="red.300">
              <FaRegTrashAlt/> Clear Session
            </Button>
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={isLoading}
              />
              <IconButton
                colorScheme="blue"
                aria-label="Send message"
                onClick={handleSend}
                loading={isLoading}
              >
                <LuSearch />
              </IconButton>
            </Flex>
          </Box>
        </VStack>
      </Box>
    </Container>
  );
}; 