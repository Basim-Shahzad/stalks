import { Card, Title } from "@mantine/core";

const formatPKR = (value: number) =>
   new Intl.NumberFormat("en-PK", {
      style: "currency",
      currency: "PKR",
      maximumFractionDigits: 0,
   }).format(value);

interface StatCardProps {
   title: string;
   stat: number;
   isCurrency: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({ title, stat, isCurrency }) => {
   return (
      <Card padding="lg" style={{ borderLeft: "4px solid blue", width: 300 }} withBorder className="">
         <Title size={15} style={{ fontWeight: "normal", color: "gray" }}>
            {title.toUpperCase()}
         </Title>

         <Title size={35} className="text-gray-800">
            {isCurrency ? formatPKR(stat) : stat}
         </Title>
      </Card>
   );
};
