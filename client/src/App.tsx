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
import AG2Client from './AG2Client';

const ag2 = new AG2Client();

export default function App() {
  const handleSendMessage = async (message: string): Promise<string> => {
    console.log("handleSendMessage: ", message);
    return await ag2.AG2_Chat(message);
  };

  const handleNewSession = async () => {
    console.log("handleNewSession");
    const res = await ag2.AG2_NewSession("new session");
    if (res === true) {
      handleRefresh();
    }
  };

  const handleGetCompanyList = async () => {
    console.log("handleGetCompanyList");
    await ag2.AG2_GetResults("get company list");
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
