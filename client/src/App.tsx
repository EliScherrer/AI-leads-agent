import {
  Box,
  ClientOnly,
  Heading,
  Skeleton,
  VStack,
} from '@chakra-ui/react'
import { ColorModeToggle } from './components/color-mode-toggle'
import { ChatWindow } from './components/ChatWindow';
import axios from 'axios';

const BASE_URL = "http://127.0.0.1:8000/chat";

export default function App() {

  const requestAG2 = async (message: string): Promise<string> => {
    console.log("requestAG2: ", message);
    
    try {
      const data = { message: message };
      const config = { headers: { 'Access-Control-Allow-Origin' : '*' } }
      const response = await axios.post(BASE_URL, data, config)

      console.log("data...");
      console.log(response.data);
      console.log("data.response...");
      console.log(response.data.response);

      return response.data.response;
    } catch (error) {
      console.log(error);
      return "Error contacting AG2";
    }
  };

  const handleSendMessage = async (message: string): Promise<string> => {
    console.log("handleSendMessage: ", message);
    return await requestAG2(message);
  };

  return (
    <Box textAlign="center" fontSize="xl">
      {/* <VStack gap="8"> */}
      <VStack>
        <Heading size="2xl" letterSpacing="tight">
          Welcome to the Lead Finder chat bot
        </Heading>

        <Box w="full" maxW="container.md">
          <ChatWindow onSendMessage={handleSendMessage} />
        </Box>
      </VStack>

      <Box pos="absolute" top="4" right="4">
        <ClientOnly fallback={<Skeleton w="10" h="10" rounded="md" />}>
          <ColorModeToggle />
        </ClientOnly>
      </Box>
    </Box>
  )
}
