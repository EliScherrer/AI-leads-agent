import axios from 'axios';

const BASE_URL = "http://127.0.0.1:8000";

export default class AG2Client {
    AG2_Chat = async (message: string): Promise<string> => {
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
    
      AG2_NewSession = async (message: string): Promise<boolean> => {
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
    
    AG2_GetResults = async (): Promise<string> => {
        console.log("AG2_GetResults");
        
        try {
          const config = { headers: { 'Access-Control-Allow-Origin' : '*' } }
          const response = await axios.get(BASE_URL + "/results", config)
    
          console.log("data...");
          console.log(response.data);
    
          return response.data;
        } catch (error) {
          console.log(error);
          return "couldn't get results";
        }
      };

}
