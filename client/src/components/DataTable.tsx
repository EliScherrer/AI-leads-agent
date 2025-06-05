import {
  Box,
  Text,
  HStack,
  Input,
  Table,
  Button,
  Icon,
} from '@chakra-ui/react';
import { useState } from 'react';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';

interface DataTableProps {
  data: LeadInfo[];
}

export interface LeadInfo {
    name: string;
    title: string;
    email: string;
    phone: string;
    linkedin: string;
    relevant_info: string;
    relevance_score: number;
    approach_reccomendation: string;
    company_info: {
      name: string;
      website: string;
      description: string;
      industry: string;
      relevant_info: string;
    };
  }

type SortDirection = 'asc' | 'desc' | 'none';

interface SortConfig {
  key: string;
  direction: SortDirection;
}

export const DataTable = ({ data }: DataTableProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: '', direction: 'none' });

  // Get headers from the first object's keys
  const headers = data.length > 0 ? Object.keys(data[0]) : [];

  const handleSort = (key: string) => {
    let direction: SortDirection = 'asc';
    
    if (sortConfig.key === key) {
      if (sortConfig.direction === 'asc') direction = 'desc';
      else if (sortConfig.direction === 'desc') direction = 'none';
      else direction = 'asc';
    }
    
    setSortConfig({ key, direction });
  };

  const getSortedData = (data: LeadInfo[]) => {
    if (sortConfig.direction === 'none') return data;

    return [...data].sort((a, b) => {
      let aValue = a[sortConfig.key as keyof LeadInfo];
      let bValue = b[sortConfig.key as keyof LeadInfo];

      // Handle nested company_info
      if (sortConfig.key === 'company_info') {
        aValue = a.company_info.name;
        bValue = b.company_info.name;
      }

      // Convert to strings for comparison
      const aString = String(aValue).toLowerCase();
      const bString = String(bValue).toLowerCase();

      if (aString < bString) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aString > bString) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  // Filter data based on search term
  const filteredData = data.filter(row =>
    Object.values(row).some(value =>
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  // Sort the filtered data
  const sortedAndFilteredData = getSortedData(filteredData);

  const handleDownload = () => {
    console.log("Downloading leads list");
  }

  const getSortIcon = (header: string) => {
    if (sortConfig.key !== header) return <Icon as={FaSort} ml={2} color="gray.400" />;
    if (sortConfig.direction === 'asc') return <Icon as={FaSortUp} ml={2} color="blue.500" />;
    if (sortConfig.direction === 'desc') return <Icon as={FaSortDown} ml={2} color="blue.500" />;
    return <Icon as={FaSort} ml={2} color="gray.400" />;
  };

  const renderRow = (lead: LeadInfo, rowIndex: number) => (
    <Table.Row 
      key={rowIndex}
      _hover={{ bg: 'gray.50' }}
      _even={{ bg: 'gray.50' }}
    >
      <Table.Cell 
        color="gray.500" 
        textAlign="center" 
        width="50px"
      >
        {rowIndex + 1}
      </Table.Cell>
      {headers.map((header, cellIndex) => (
        <Table.Cell 
          key={cellIndex}
          px={3}
          py={2}
          fontSize="sm"
          minW="150px"
          maxW="300px"
          overflow="hidden"
          textOverflow="ellipsis"
          whiteSpace="nowrap"
          color="gray.500"
          title={header === "company_info" ? JSON.stringify(lead[header as keyof LeadInfo], null, 2) : String(lead[header as keyof LeadInfo])}
        >
          {header === "company_info" ? String(lead["company_info"]["name"]) : String(lead[header as keyof LeadInfo])}
        </Table.Cell>
      ))}
    </Table.Row>
  );

  return (
    <Box borderWidth="1px" borderRadius="lg" overflow="hidden" bg="white" mb={50}>
      <HStack mb={4} justify="space-between" p={4} borderBottomWidth="1px">
        <Text color="gray.600" fontSize="sm">
          {sortedAndFilteredData.length} / {data.length} Rows Selected
        </Text>
        <Input
          placeholder="Search..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          maxW="300px"
          size="sm"
          borderRadius="md"
          color="gray.500"
        />
      </HStack>

      <Box overflowX="auto">
        <Table.Root variant="outline" size="sm" w="full" interactive showColumnBorder>
          <Table.Header>
            <Table.Row bg="gray.50">
              <Table.ColumnHeader width="50px" textAlign="center">#</Table.ColumnHeader>
              {headers.map((header, index) => (
                <Table.ColumnHeader 
                  key={index}
                  px={3}
                  py={2}
                  fontSize="sm"
                  fontWeight="medium"
                  textTransform="none"
                  color="gray.700"
                  minW="150px"
                  cursor="pointer"
                  onClick={() => handleSort(header)}
                  _hover={{ bg: 'gray.100' }}
                >
                  <HStack gap={1} justify="space-between">
                    <Text>{header.replace(/_/g, ' ')}</Text>
                    {getSortIcon(header)}
                  </HStack>
                </Table.ColumnHeader>
              ))}
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {sortedAndFilteredData.map((row, rowIndex) =>
              renderRow(row, rowIndex)
            )}
          </Table.Body>
        </Table.Root>
      </Box>
      <Button
        colorScheme="green"
        size="lg"
        onClick={handleDownload}
      >
        Download Leads List
      </Button>
    </Box>
  );
}; 