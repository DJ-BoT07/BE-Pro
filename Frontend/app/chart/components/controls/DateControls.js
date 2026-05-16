import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export function DateControls({ selectedDate, onDateChange }) {
  // Set default date to January 3, 2024 (start of available data)
  // Available data range: 2024-01-03 to 2024-10-31
  const defaultDate = new Date(2024, 0, 3);
  const dateToUse = selectedDate || defaultDate;

  // Validate date is within available range
  const minDate = new Date(2024, 0, 3);
  const maxDate = new Date(2024, 9, 31);

  const handleDateChange = (days) => {
    const newDate = new Date(dateToUse);
    newDate.setDate(newDate.getDate() + days);
    
    // Constrain date to available range
    if (newDate < minDate) {
      onDateChange(minDate);
    } else if (newDate > maxDate) {
      onDateChange(maxDate);
    } else {
      onDateChange(newDate);
    }
  };

  return (
    <div className="flex items-center gap-2 mb-4">
      <Button
        onClick={() => handleDateChange(-1)}
        className="bg-blue-500/20 hover:bg-blue-500/30 text-white"
      >
        Previous Day
      </Button>

      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={`w-[240px] justify-start text-left font-normal bg-blue-500/20 hover:bg-blue-500/30 text-white`}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {format(dateToUse, 'dd MMMM yyyy')}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0 bg-zinc-950 border-zinc-800">
          <Calendar
            mode="single"
            selected={dateToUse}
            onSelect={(date) => {
              if (date) {
                // Validate date is within range
                if (date < minDate) {
                  onDateChange(minDate);
                } else if (date > maxDate) {
                  onDateChange(maxDate);
                } else {
                  onDateChange(date);
                }
              }
            }}
            initialFocus
            defaultMonth={defaultDate}
            disabled={(date) => date < minDate || date > maxDate}
          />
        </PopoverContent>
      </Popover>

      <Button
        onClick={() => handleDateChange(1)}
        className="bg-blue-500/20 hover:bg-blue-500/30 text-white"
      >
        Next Day
      </Button>
    </div>
  );
}