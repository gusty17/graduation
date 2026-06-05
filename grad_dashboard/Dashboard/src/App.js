import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { WiFiCSIProvider } from "./context/WiFiCSIContext";

import DashboardScreen from "./screens/Dashboard/DashboardScreen";
import AnalyticsScreen from "./screens/Analytics/AnalyticsScreen";

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <WiFiCSIProvider>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Dashboard" component={DashboardScreen} />
          <Stack.Screen name="Analytics" component={AnalyticsScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </WiFiCSIProvider>
  );
}
