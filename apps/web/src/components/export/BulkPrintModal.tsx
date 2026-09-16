import React, { useState } from 'react';
import { downloadPdfGrid, downloadBulkPdfZip } from '../../lib/api';
import { FileText, Download, X, Printer, Archive, Layers } from 'lucide-react';

interface BulkPrintModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BulkPrintModal: React.FC<BulkPrintModalProps> = ({ isOpen, onClose }) => {
  const [formType, setFormType] = useState<'appendix_4b' | 'appendix_6' | 'appendix_7' | 'incident' | 'bulk_zip'>('appendix_4b');
  const [roomCode, setRoomCode] = useState('101');
  const [piName, setPiName] = useState('Dr. Windsor');
  const [auppNumber, setAuppNumber] = useState('AUPP-2026-001');
  const [species, setSpecies] = useState('Zebrafish');
  const [weekOf, setWeekOf] = useState('2026-W38');
  const [selectedRooms, setSelectedRooms] = useState<string[]>(['101', '102']);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleDownload = async () => {
    try {
      setLoading(true);
      if (formType === 'bulk_zip') {
        const response = await downloadBulkPdfZip(selectedRooms);
        const blob = new Blob([response.data], { type: 'application/zip' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `ACARE_PaperGrid_Bundle_${new Date().toISOString().slice(0, 10)}.zip`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } else {
        const response = await downloadPdfGrid({
          form_type: formType,
          room_code: roomCode,
          pi_name: piName,
          aupp_number: auppNumber,
          species,
          week_of: weekOf,
        });
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const formNames: Record<string, string> = {
          appendix_4b: `Appendix_4b_Census_Room_${roomCode}`,
          appendix_6: `Appendix_6_WaterQuality_Room_${roomCode}`,
          appendix_7: `Appendix_7_TestStrips_Room_${roomCode}`,
          incident: `Aquatic_Incident_Report`,
        };
        link.setAttribute('download', `${formNames[formType]}_${new Date().toISOString().slice(0, 10)}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to generate PDF. Please verify parameters and try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleRoom = (room: string) => {
    setSelectedRooms((prev) =>
      prev.includes(room) ? prev.filter((r) => r !== room) : [...prev, room]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full overflow-hidden border border-gray-200">
        {/* Modal Header */}
        <div className="bg-[#005596] px-6 py-4 flex items-center justify-between text-white">
          <div className="flex items-center space-x-3">
            <Printer className="w-6 h-6 text-[#FFCE00]" />
            <div>
              <h2 className="text-lg font-bold">Paper-Grid PDF & Bulk Print Center</h2>
              <p className="text-xs text-blue-100">Generate UWindsor Official Physical Record Form Layouts</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200 p-1 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Form Selection Radio Cards */}
          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
              Select Record Form Layout
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'appendix_4b', label: 'Appendix 4b', sub: '21-Row Daily Census & Log', icon: FileText },
                { id: 'appendix_6', label: 'Appendix 6', sub: 'Daily Water Quality Week Grid', icon: Layers },
                { id: 'appendix_7', label: 'Appendix 7', sub: 'Aquarium Test Strips Log', icon: FileText },
                { id: 'incident', label: 'Incident Report', sub: 'Single Event Aquatic Report', icon: FileText },
                { id: 'bulk_zip', label: 'Multi-Room ZIP', sub: 'Export All Grid PDFs Bundle', icon: Archive },
              ].map((item) => {
                const Icon = item.icon;
                const isSelected = formType === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setFormType(item.id as any)}
                    className={`p-3 rounded-lg border text-left transition-all flex items-start space-x-3 ${
                      isSelected
                        ? 'border-[#005596] bg-[#E6F0F7] ring-2 ring-[#005596]'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <Icon className={`w-5 h-5 mt-0.5 ${isSelected ? 'text-[#005596]' : 'text-gray-400'}`} />
                    <div>
                      <div className="text-sm font-bold text-gray-900">{item.label}</div>
                      <div className="text-xs text-gray-500">{item.sub}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Form Options Inputs */}
          {formType !== 'bulk_zip' ? (
            <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Room Code</label>
                <input
                  type="text"
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-[#005596]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Principal Investigator</label>
                <input
                  type="text"
                  value={piName}
                  onChange={(e) => setPiName(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-[#005596]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">AUPP #</label>
                <input
                  type="text"
                  value={auppNumber}
                  onChange={(e) => setAuppNumber(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-[#005596]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Species</label>
                <input
                  type="text"
                  value={species}
                  onChange={(e) => setSpecies(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-[#005596]"
                />
              </div>
              {formType === 'appendix_6' && (
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Week Of</label>
                  <input
                    type="text"
                    value={weekOf}
                    onChange={(e) => setWeekOf(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-[#005596]"
                  />
                </div>
              )}
            </div>

          ) : (
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <label className="block text-xs font-bold text-gray-700 mb-2">Select Rooms for Export Bundle</label>
              <div className="flex space-x-3">
                {['101', '102', '103', '104'].map((rm) => (
                  <button
                    key={rm}
                    type="button"
                    onClick={() => toggleRoom(rm)}
                    className={`px-4 py-2 text-sm font-semibold rounded-md border transition-all ${
                      selectedRooms.includes(rm)
                        ? 'bg-[#005596] text-white border-[#005596]'
                        : 'bg-white text-gray-700 border-gray-300'
                    }`}
                  >
                    Room {rm}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="bg-gray-100 px-6 py-4 flex justify-between items-center border-t border-gray-200">
          <div className="text-xs text-gray-500 font-medium">
            Format: PDF / Vector High-Resolution Print Ready
          </div>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDownload}
              disabled={loading}
              className="px-5 py-2 text-sm font-bold text-white bg-[#005596] hover:bg-[#003A66] rounded-lg shadow-md flex items-center space-x-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <span>Generating...</span>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>{formType === 'bulk_zip' ? 'Download Bundle (.ZIP)' : 'Download PDF Form'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
