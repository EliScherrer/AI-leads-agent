import {
  Box,
  ClientOnly,
  Heading,
  Skeleton,
  VStack,
} from '@chakra-ui/react'
import { ColorModeToggle } from './components/color-mode-toggle'
import { ChatWindow } from './components/ChatWindow';

export default function Page() {
  const handleSendMessage = async (message: string): Promise<string> => {
    // TODO: Make API call to the backend
    await new Promise(resolve => setTimeout(resolve, 1000));
    return `You said: ${message}`;
  };

  return (
    <Box textAlign="center" fontSize="xl" pt="10vh">
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
