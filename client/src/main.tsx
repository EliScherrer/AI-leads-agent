import { ChakraProvider, defaultSystem } from "@chakra-ui/react"
// import { ThemeProvider } from "next-themes"
import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import { ColorModeProvider } from "./components/color-mode"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ChakraProvider value={defaultSystem}>
      <ColorModeProvider attribute="class" defaultTheme="light" disableTransitionOnChange>
        <App />
      </ColorModeProvider>
    </ChakraProvider>
  </React.StrictMode>,
)
