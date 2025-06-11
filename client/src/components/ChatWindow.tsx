import { useState, useRef } from 'react';
import { Box, VStack, Input, IconButton, Flex, Text, Avatar, Container, Button } from '@chakra-ui/react';
import { LuSearch } from 'react-icons/lu';
import { FaRegTrashAlt, FaUser } from "react-icons/fa";
import { AiOutlineCloudUpload } from "react-icons/ai";
import AG2Client from '../AG2Client';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

const defaultFirstMessage: Message = {
  id: Date.now().toString(),
  text: "Hello, I'm the lead finder chat bot. I'm here to help you find leads for your product. Please provide me with information about your company, the product you are selling, and information about your ideal customer profile. You can also upload a CSV or TSV file with your data.",
  sender: 'ai',
  timestamp: new Date(),
};

const ag2 = new AG2Client();

export const ChatWindow = ({ } ) => {
  const [messages, setMessages] = useState<Message[]>([defaultFirstMessage]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Trigger the file input when the button is clicked
  const handleUploadData = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  // Handle file selection
  const launchFileSelector = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileName = file.name.toLowerCase();
    const isTSV = fileName.endsWith('.tsv') || fileName.endsWith('.txt');
    if (!isTSV) {
      alert('Please upload a .tsv file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      if (!text) return;

      const jsonString = tsvToJsonString(text);
      if (!jsonString) {
        return;
      };

      sendMessage(jsonString);
    };
    
    reader.readAsText(file);
  };

  function tsvToJsonString(tsvString: string) {
    const delimiter = '\t';

    const rows = tsvString.split("\n");
    const headers = rows[0].split(delimiter);
    const jsonData = [];

    if (rows.length < 2) {
      alert('File must have a header and at least one row.');
      return;
    }

    for (let i = 1; i < rows.length; i++) {
        if (!rows[i]) {
            continue;
        }

        const values = rows[i].split(delimiter);
        const obj: any = {};

        for (let j = 0; j < headers.length; j++) {
            const key: string = (headers[j]) ? headers[j].trim() : "";
            const value: string = (values[j]) ? values[j].trim() : "";
            obj[key] = value;
        }

        jsonData.push(obj);
    }
    console.log("uploaded data: ");
    console.log(jsonData);
    return JSON.stringify(jsonData);
}

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const aiResponseMessage = await ag2.AG2_Chat(message);
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
      sendMessage(inputValue);
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
        borderWidth="2px"
        borderRadius="lg"
        borderColor="gray.950"
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
                        <Avatar.Root size="lg" borderWidth="1px" borderColor="gray.600" bg="white">
                            {/* <Avatar.Fallback name={message.sender === 'user' ? 'User' : 'AI'} /> */}
                            {(message.sender === 'ai') && <Avatar.Image src="https://platform.theverge.com/wp-content/uploads/sites/2/2025/02/openai-old-logo.png?quality=90&strip=all&crop=7.8125%2C0%2C84.375%2C100&w=2400" />}
                            {(message.sender === 'user') && <FaUser />}
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
            </VStack>
          </Box>

          {/* Input Area */}
          <Box
            w="full"
            p={4}
            borderTopWidth="2px"
            borderColor="gray.950"
          >
            <Flex gap={2}>
              <Button onClick={handleNewSession} bg="red.500" _hover={{ bg: 'red.600' }}>
                <FaRegTrashAlt/> Clear Session
              </Button>
              <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isLoading}
                  borderWidth="1px"
                  borderColor="gray.950"
              />
              <IconButton
                  colorScheme="blue"
                  aria-label="Send message"
                  onClick={() => sendMessage(inputValue)}
                  loading={isLoading}
              ><LuSearch /></IconButton>
              <Button
                bg="blue.500"
                _hover={{ bg: 'blue.600' }}
                onClick={handleUploadData}
              ><AiOutlineCloudUpload/>Upload Data</Button>
            </Flex>
          </Box>
        </VStack>
      </Box>
      {/* Hidden file input */}
      <input
        type="file"
        accept=".csv,.tsv,text/csv,text/tab-separated-values"
        style={{ display: 'none' }}
        ref={fileInputRef}
        onChange={launchFileSelector}
      />
    </Container>
  );
}; 