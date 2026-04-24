import { Drawer, NumberInput, Stack, Text, Divider, Box, Paper } from "@mantine/core";
import { useSettings } from "../hooks/useSettings";

const Settings = ({ opened, close }: any) => {
   const { increaseByPercInSell, setIncreaseByPercInSell } = useSettings();

   return (
      <Drawer
         opened={opened}
         onClose={close}
         position="right"
         size="md"
         title={
            <Text size="xl" style={{ letterSpacing: "1px" }}>
               SETTINGS
            </Text>
         }
         padding="xl"
         styles={{
            header: { borderBottom: "1px solid #eee", marginBottom: "20px", paddingBottom: "15px" },
            content: { backgroundColor: "#f9f9f9" },
         }}>
         <Stack gap="xl">
            <Box>
               <Paper withBorder p="md" radius="md" shadow="xs">
                  <NumberInput
                     label="Sell Threshold Increase"
                     description="The minimum % gain required to suggest a sell"
                     value={increaseByPercInSell}
                     onChange={(val) => setIncreaseByPercInSell(Number(val))}
                     step={0.01}
                     min={0}
                     max={100}
                     fixedDecimalScale
                     rightSection={
                        <Text size="xs" c="dimmed" pr="md">
                           %
                        </Text>
                     }
                     size="sm"
                     variant="filled"
                  />
               </Paper>
            </Box>
         </Stack>
      </Drawer>
   );
};

export default Settings;
