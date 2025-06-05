import {
  Box,
  Button,
  ClientOnly,
  Heading,
  Skeleton,
  VStack,
} from '@chakra-ui/react'
import { ColorModeToggle } from './components/color-mode-toggle'
import { ChatWindow } from './components/ChatWindow';
import axios from 'axios';

const BASE_URL = "http://127.0.0.1:8000";

export default function App() {

  const AG2_Chat = async (message: string): Promise<string> => {
    console.log("AG2_Chat: ", message);

    try {
      const data = { message: message };
      const config = { headers: { 'Access-Control-Allow-Origin' : '*' } }
      const response = await axios.post(BASE_URL + "/chat", data, config)

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

  const AG2_NewSession = async (message: string): Promise<boolean> => {
    console.log("AG2_NewSession: ", message);
    
    try {
      const data = { new: "true" };
      const config = { headers: { 'Access-Control-Allow-Origin' : '*' } }
      const response = await axios.post(BASE_URL + "/new_session", data, config)

      console.log("data...");
      console.log(response.data);
      console.log("data.response...");
      console.log(response.data.response);

      return true;
    } catch (error) {
      console.log(error);
      return false;
    }
  };

  const AG2_GetCompanyList = async (message: string): Promise<boolean> => {
    console.log("AG2_GetCompanyList: ", message);
    
    try {
      const config = { headers: { 'Access-Control-Allow-Origin' : '*' } }
      const response = await axios.get(BASE_URL + "/companies", config)

      console.log("data...");
      console.log(response.data);
      console.log("data.response...");
      console.log(response.data.response);

      return true;
    } catch (error) {
      console.log(error);
      return false;
    }
  };

  const handleSendMessage = async (message: string): Promise<string> => {
    console.log("handleSendMessage: ", message);
    return await AG2_Chat(message);
  };

  const handleNewSession = async () => {
    console.log("handleNewSession");
    const res = await AG2_NewSession("new session");
    if (res === true) {
      handleRefresh();
    }
  };

  const handleGetCompanyList = async () => {
    console.log("handleGetCompanyList");
    await AG2_GetCompanyList("get company list");
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <Box textAlign="center" fontSize="xl">
      <VStack gap={8}>
        <Heading size="2xl" letterSpacing="tight">
          Welcome to the Lead Finder chat bot
        </Heading>

        <Button
          colorScheme="blue"
          size="lg"
          onClick={handleNewSession}
        >
          New Session
        </Button>

        <Button
          colorScheme="green"
          size="lg"
          onClick={handleGetCompanyList}
        >
          Get Company List
        </Button>

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
