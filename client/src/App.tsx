import {
  Box,
  Button,
  ClientOnly,
  Heading,
  Skeleton,
  VStack,
  Text
} from '@chakra-ui/react'
import { ColorModeToggle } from './components/color-mode-toggle'
import { ChatWindow } from './components/ChatWindow';
import AG2Client from './AG2Client';
import { DataTable, LeadInfo } from './components/DataTable';
import { useRef, useState } from 'react';
import { AiOutlineCloudDownload } from "react-icons/ai";

const ag2 = new AG2Client();

export default function App() {
  const [tableData, setTableData] = useState<LeadInfo[]>([]);
  const [isLoadingLeads, setIsLoadingLeads] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  const handleGetLeads = async () => {
    console.log("handleGetLeads");
    setIsLoadingLeads(true);
    try {
      const leads: string = await ag2.AG2_GetResults();

      if (leads === "couldn't get results" || leads === "Leads haven't been generated yet") {
        console.log("Leads not ready");
        return;
      }

      const leadsList = JSON.parse(leads);

      console.log("leadsListLength: ", leadsList.leads_list.length);
      console.log(leadsList.leads_list[0]);
      console.log(leadsList.leads_list[0].lead_info);
      console.log(Object.keys(leadsList.leads_list[0]));

      setTableData(leadsList.leads_list);
    } catch (error) {
      console.error("Error getting leads: ", error);
    } finally {
      setIsLoadingLeads(false);
      scrollToBottom();
    }
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <Box textAlign="center" fontSize="xl">
      <VStack gap={8}>
        <Heading size="5xl" letterSpacing="tight" paddingTop="50px">
          Sales Lead Finder Chat Bot
        </Heading>
        <Box w="full" maxW="container.md">
          <ChatWindow />
        </Box>
        {tableData.length === 0 && <Box
          id="get-leads-list-explanation"
          p={8}
          bg="gray.300"
          borderRadius="xl"
          boxShadow="lg"
          borderWidth="1px"
          borderColor="gray.200"
          maxW="full"
          mx={8}
          my={6}
          display="flex"
          flexDirection="column"
          alignItems="center"
          gap={6}
        >
          <Text
            fontSize="lg"
            color="gray.950"
            mb={2}
            textAlign="center"
            fontWeight="medium"
          >
            When the chat bot tells you that the intake data has been collected, you can click the button below to get the leads list. It usually takes about 2 minutes after the intake data has been collected to generate the leads list.
          </Text>
          <Button
              size="lg"
              fontWeight="bold"
              px={8}
              boxShadow="md"
              mt={2}
              bg="teal.500"
              _hover={{ bg: 'teal.600' }}
              pos="absolute" bottom="14" right="10"
              loading={isLoadingLeads}
              disabled={isLoadingLeads}
              onClick={handleGetLeads}
            >
              <AiOutlineCloudDownload /> Show Leads List
            </Button>
        </Box>}

        <Box w="full">
          {tableData.length > 0 && <DataTable data={tableData} />}
        </Box>
        <div ref={bottomRef} />
      </VStack>

      <Box pos="absolute" top="4" right="4">
        <ClientOnly fallback={<Skeleton w="10" h="10" rounded="md" />}>
          <ColorModeToggle />
        </ClientOnly>
      </Box>
    </Box>
  )
}
