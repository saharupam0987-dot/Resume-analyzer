import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Users, Plus, BookOpen, GraduationCap, Trash2, Calendar, 
  Search, Check, X, ChevronRight, ArrowRight, ShieldCheck, 
  FileText, Clock, AlertCircle, Sparkles, UserPlus, UserMinus, 
  Layers, ExternalLink, RefreshCw 
} from 'lucide-react';
import API from '../api';
import { Card, Badge, Button, SectionTitle, EmptyState, Skeleton, useToast } from './ui';

export default function ClassManagement({ role, exams = [], onStartExam, onViewExam, onRefreshExams }) {
  const toast = useToast();
  const isTeacher = role === 'teacher';

  // Core State
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Teacher Modals & Detail View
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newClassName, setNewClassName] = useState('');
  const [newClassDesc, setNewClassDesc] = useState('');
  const [creating, setCreating] = useState(false);

  // Selected Class Management Drawer/Modal
  const [selectedClass, setSelectedClass] = useState(null);
  const [classTab, setClassTab] = useState('students'); // 'students' | 'exams'
  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [availableStudents, setAvailableStudents] = useState([]);
  const [selectedStudentToAdd, setSelectedStudentToAdd] = useState('');
  const [addingStudent, setAddingStudent] = useState(false);

  // Class Exams State
  const [classExams, setClassExams] = useState([]);
  const [loadingClassExams, setLoadingClassExams] = useState(false);
  const [selectedExamToAssign, setSelectedExamToAssign] = useState('');
  const [assignmentDueDate, setAssignmentDueDate] = useState('');
  const [assigningExam, setAssigningExam] = useState(false);

  // Fetch classes based on role
  const fetchClasses = useCallback(async () => {
    setLoading(true);
    try {
      const endpoint = isTeacher ? '/classes' : '/student/classes';
      const res = await API.get(endpoint);
      setClasses(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to load classes:', err);
      toast?.push?.(err.response?.data?.detail || 'Could not load classes', 'error');
      setClasses([]);
    } finally {
      setLoading(false);
    }
  }, [isTeacher]);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  // Teacher: Load available registered students for enrollment
  const fetchAvailableStudents = useCallback(async () => {
    if (!isTeacher) return;
    try {
      const res = await API.get('/classes/available-students');
      setAvailableStudents(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to fetch students directory:', err);
      setAvailableStudents([]);
    }
  }, [isTeacher]);

  useEffect(() => {
    if (isTeacher) {
      fetchAvailableStudents();
    }
  }, [isTeacher, fetchAvailableStudents]);

  // Teacher: Fetch enrolled students for selected class
  const fetchClassStudents = useCallback(async (classId) => {
    setLoadingStudents(true);
    try {
      const res = await API.get(`/classes/${classId}/students`);
      setEnrolledStudents(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to fetch class students:', err);
      toast?.push?.(err.response?.data?.detail || 'Could not load students for this class', 'error');
      setEnrolledStudents([]);
    } finally {
      setLoadingStudents(false);
    }
  }, []);

  // Fetch exams assigned to selected class (works for both Teacher and Student)
  const fetchClassExams = useCallback(async (classId) => {
    setLoadingClassExams(true);
    try {
      const res = await API.get(`/classes/${classId}/exams`);
      setClassExams(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to fetch class exams:', err);
      toast?.push?.(err.response?.data?.detail || 'Could not load assigned exams for this class', 'error');
      setClassExams([]);
    } finally {
      setLoadingClassExams(false);
    }
  }, []);

  // Open class detail view
  const handleOpenClass = (cls) => {
    setSelectedClass(cls);
    if (isTeacher) {
      setClassTab('students');
      fetchClassStudents(cls.id);
      fetchClassExams(cls.id);
    } else {
      setClassTab('exams');
      fetchClassExams(cls.id);
    }
  };

  // Close class detail view
  const handleCloseClass = () => {
    setSelectedClass(null);
    setEnrolledStudents([]);
    setClassExams([]);
  };

  // Teacher: Create Classroom
  const handleCreateClass = async (e) => {
    e.preventDefault();
    const name = newClassName.trim();
    if (!name) {
      toast.push('Classroom name is required', 'error');
      return;
    }

    setCreating(true);
    try {
      const res = await API.post('/classes', {
        name,
        description: newClassDesc.trim(),
      });
      toast.push(`Classroom "${res.data.name}" created successfully!`, 'success');
      setNewClassName('');
      setNewClassDesc('');
      setCreateModalOpen(false);
      fetchClasses();
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to create classroom', 'error');
    } finally {
      setCreating(false);
    }
  };

  // Teacher: Delete Classroom
  const handleDeleteClass = async (classId, className) => {
    if (!window.confirm(`Are you sure you want to delete "${className}"? This will unassign all exams and remove enrolled students from this cohort.`)) {
      return;
    }

    try {
      await API.delete(`/classes/${classId}`);
      toast.push(`Classroom "${className}" deleted`, 'success');
      if (selectedClass?.id === classId) {
        handleCloseClass();
      }
      fetchClasses();
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to delete classroom', 'error');
    }
  };

  // Teacher: Enroll Student
  const handleEnrollStudent = async () => {
    if (!selectedClass || !selectedStudentToAdd) return;
    setAddingStudent(true);
    try {
      await API.post(`/classes/${selectedClass.id}/students/${selectedStudentToAdd}`);
      toast.push('Student enrolled successfully!', 'success');
      setSelectedStudentToAdd('');
      fetchClassStudents(selectedClass.id);
      fetchClasses(); // Update student count badge
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to enroll student', 'error');
    } finally {
      setAddingStudent(false);
    }
  };

  // Teacher: Remove Student from Class
  const handleRemoveStudent = async (studentId, studentName) => {
    if (!selectedClass) return;
    if (!window.confirm(`Remove ${studentName} from "${selectedClass.name}"?`)) return;

    try {
      await API.delete(`/classes/${selectedClass.id}/students/${studentId}`);
      toast.push(`${studentName} removed from class`, 'success');
      fetchClassStudents(selectedClass.id);
      fetchClasses(); // Update student count badge
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to remove student', 'error');
    }
  };

  // Teacher: Assign Exam to Class
  const handleAssignExam = async () => {
    if (!selectedClass || !selectedExamToAssign) return;
    setAssigningExam(true);
    try {
      const payload = {};
      if (assignmentDueDate) {
        payload.due_date = new Date(assignmentDueDate).toISOString();
      }

      await API.post(`/exams/${selectedExamToAssign}/assign/${selectedClass.id}`, payload);
      toast.push('Exam assigned to class successfully!', 'success');
      setSelectedExamToAssign('');
      setAssignmentDueDate('');
      fetchClassExams(selectedClass.id);
      fetchClasses(); // Update exam count badge
      if (onRefreshExams) onRefreshExams();
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to assign exam', 'error');
    } finally {
      setAssigningExam(false);
    }
  };

  // Teacher: Unassign Exam from Class
  const handleUnassignExam = async (examId, examTitle) => {
    if (!selectedClass) return;
    if (!window.confirm(`Unassign "${examTitle}" from "${selectedClass.name}"? Students in this class will no longer be able to take it.`)) return;

    try {
      await API.delete(`/exams/${examId}/assign/${selectedClass.id}`);
      toast.push(`Exam unassigned from ${selectedClass.name}`, 'success');
      fetchClassExams(selectedClass.id);
      fetchClasses(); // Update exam count badge
      if (onRefreshExams) onRefreshExams();
    } catch (err) {
      toast.push(err.response?.data?.detail || 'Failed to unassign exam', 'error');
    }
  };

  // Filtered classes list
  const filteredClasses = useMemo(() => {
    if (!searchQuery) return classes;
    const q = searchQuery.toLowerCase();
    return classes.filter(
      (c) => c.name?.toLowerCase().includes(q) || c.description?.toLowerCase().includes(q)
    );
  }, [classes, searchQuery]);

  // Students not yet enrolled in the selected class
  const unEnrolledStudents = useMemo(() => {
    const enrolledIds = new Set(enrolledStudents.map((s) => s.id));
    return availableStudents.filter((s) => !enrolledIds.has(s.id));
  }, [availableStudents, enrolledStudents]);

  // Exams not yet assigned to the selected class
  const unAssignedExams = useMemo(() => {
    const assignedIds = new Set(classExams.map((e) => e.id));
    return exams.filter((e) => !assignedIds.has(e.id));
  }, [exams, classExams]);

  return (
    <div className="space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
            {isTeacher ? 'Cohort & Access Control' : 'Enrolled Academics'}
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1">
            {isTeacher ? 'Classrooms & Cohorts' : 'My Classes & Courses'}
          </h1>
          <p className="text-xs sm:text-sm text-[#616B66] mt-1 font-sans">
            {isTeacher 
              ? 'Organize student groups, assign specific examination papers, and enforce private cohort access boundaries.'
              : 'Browse your enrolled classrooms and access examinations assigned exclusively to your student cohorts.'
            }
          </p>
        </div>

        {isTeacher && (
          <Button variant="primary" onClick={() => setCreateModalOpen(true)} icon={Plus}>
            Create Class
          </Button>
        )}
      </div>

      {/* Search & Controls */}
      <div className="flex items-center gap-3 max-w-md">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#969E99]" />
          <input 
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E7E4DC] text-xs sm:text-sm bg-white focus:border-[#16382C] outline-none transition-colors" 
            placeholder={isTeacher ? "Search classrooms by name or description…" : "Search your classes…"}
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
          />
        </div>
        <Button variant="outline" size="sm" onClick={fetchClasses} icon={RefreshCw} title="Refresh classes" />
      </div>

      {/* Classrooms Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-48 rounded-2xl" />)}
        </div>
      ) : filteredClasses.length === 0 ? (
        <Card>
          <EmptyState
            icon={GraduationCap}
            title={classes.length ? 'No classrooms match your search' : isTeacher ? 'No classrooms created yet' : 'You are not enrolled in any classes yet'}
            description={
              classes.length 
                ? 'Try searching with a different keyword.' 
                : isTeacher 
                ? 'Create your first classroom cohort, enroll students, and assign tailored examination papers.' 
                : 'Your teachers will enroll you into their subject cohorts so you can access assigned exams.'
            }
            action={isTeacher && classes.length === 0 ? (
              <Button variant="primary" onClick={() => setCreateModalOpen(true)} icon={Plus}>
                Create First Class
              </Button>
            ) : null}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredClasses.map((cls, idx) => (
            <div 
              key={cls.id}
              className="bg-white border border-[#E7E4DC] hover:border-[#D8D4C8] rounded-2xl p-6 transition-all duration-200 hover:shadow-sm flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-serif text-2xl font-bold text-[#16382C]">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Badge tone="sage">{cls.student_count || 0} Students</Badge>
                    <Badge tone="neutral">{cls.exam_count || 0} Exams</Badge>
                  </div>
                </div>

                <h3 className="font-serif text-lg font-medium text-[#1C2421] leading-snug line-clamp-1 group-hover:text-[#16382C] transition-colors">
                  {cls.name}
                </h3>

                <p className="text-xs text-[#616B66] mt-2 line-clamp-2 min-h-[32px]">
                  {cls.description || 'Dedicated academic cohort for exam evaluation and student assessment.'}
                </p>
              </div>

              <div className="pt-4 mt-5 border-t border-[#F5F2EA] flex items-center justify-between">
                <button
                  onClick={() => handleOpenClass(cls)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#16382C] hover:underline cursor-pointer"
                >
                  <span>{isTeacher ? 'Manage Class' : 'View Assigned Exams'}</span>
                  <ArrowRight size={13} />
                </button>

                {isTeacher && (
                  <button
                    onClick={() => handleDeleteClass(cls.id, cls.name)}
                    className="text-xs text-rose-600 hover:text-rose-800 p-1.5 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                    title="Delete classroom"
                  >
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Drawer / Modal for Selected Classroom */}
      {selectedClass && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-[#E7E4DC] overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 sm:px-8 py-5 border-b border-[#E7E4DC] flex items-center justify-between bg-[#FAF8F5]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#E8EFE9] text-[#16382C] flex items-center justify-center font-serif font-bold">
                  <GraduationCap size={20} />
                </div>
                <div>
                  <h2 className="font-serif text-xl sm:text-2xl font-normal text-[#1C2421]">
                    {selectedClass.name}
                  </h2>
                  <p className="text-xs text-[#616B66] line-clamp-1">
                    {selectedClass.description || 'Academic cohort'}
                  </p>
                </div>
              </div>

              <button
                onClick={handleCloseClass}
                className="w-8 h-8 rounded-full hover:bg-[#E7E4DC] flex items-center justify-center text-[#616B66] hover:text-[#1C2421] transition-colors cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            {/* Tabs for Teacher: Students vs Exams */}
            {isTeacher && (
              <div className="flex border-b border-[#E7E4DC] px-6 sm:px-8 bg-white">
                <button
                  onClick={() => setClassTab('students')}
                  className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                    classTab === 'students' 
                      ? 'border-[#16382C] text-[#16382C]' 
                      : 'border-transparent text-[#616B66] hover:text-[#1C2421]'
                  }`}
                >
                  Enrolled Students ({enrolledStudents.length})
                </button>
                <button
                  onClick={() => setClassTab('exams')}
                  className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                    classTab === 'exams' 
                      ? 'border-[#16382C] text-[#16382C]' 
                      : 'border-transparent text-[#616B66] hover:text-[#1C2421]'
                  }`}
                >
                  Assigned Exams ({classExams.length})
                </button>
              </div>
            )}

            {/* Modal Body */}
            <div className="p-6 sm:p-8 overflow-y-auto flex-1 space-y-6">
              {/* TAB 1: Enrolled Students (Teacher Only) */}
              {isTeacher && classTab === 'students' && (
                <div className="space-y-6">
                  {/* Enroll New Student Card */}
                  <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#E7E4DC] space-y-3">
                    <h4 className="text-xs uppercase font-bold tracking-wider text-[#16382C] flex items-center gap-2">
                      <UserPlus size={14} />
                      <span>Enroll Student into Cohort</span>
                    </h4>

                    {unEnrolledStudents.length === 0 ? (
                      <p className="text-xs text-[#969E99]">
                        {availableStudents.length === 0 
                          ? 'No registered students found in the database. When students register, they will appear here.'
                          : 'All registered students are already enrolled in this classroom.'}
                      </p>
                    ) : (
                      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                        <select
                          className="flex-1 px-3 py-2 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#1C2421] focus:border-[#16382C] outline-none"
                          value={selectedStudentToAdd}
                          onChange={(e) => setSelectedStudentToAdd(e.target.value)}
                        >
                          <option value="">-- Select student to enroll --</option>
                          {unEnrolledStudents.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} ({s.email}) · Roll: {s.roll_number}
                            </option>
                          ))}
                        </select>
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={!selectedStudentToAdd}
                          loading={addingStudent}
                          onClick={handleEnrollStudent}
                          icon={UserPlus}
                        >
                          Enroll Student
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Enrolled Students Roster */}
                  <div>
                    <h4 className="text-xs uppercase font-bold tracking-wider text-[#969E99] mb-3">
                      Current Enrolled Roster
                    </h4>

                    {loadingStudents ? (
                      <div className="space-y-2">
                        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-14 rounded-xl" />)}
                      </div>
                    ) : enrolledStudents.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-[#E7E4DC] rounded-2xl text-xs text-[#969E99]">
                        No students enrolled in this classroom yet. Use the selector above to enroll students.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {enrolledStudents.map((st) => (
                          <div 
                            key={st.id}
                            className="p-3.5 rounded-xl border border-[#E7E4DC] bg-white hover:bg-[#FAF8F5] flex items-center justify-between transition-colors text-xs"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-[#E8EFE9] text-[#16382C] font-bold flex items-center justify-center">
                                {st.name?.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <div className="font-semibold text-[#1C2421]">{st.name}</div>
                                <div className="text-[11px] text-[#969E99]">
                                  {st.email} · Roll: {st.roll_number}
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={() => handleRemoveStudent(st.id, st.name)}
                              className="text-rose-600 hover:text-rose-800 p-1.5 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer text-xs flex items-center gap-1 font-medium"
                              title="Remove student"
                            >
                              <UserMinus size={14} />
                              <span className="hidden sm:inline">Remove</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: Assigned Exams (Teacher & Student) */}
              {(!isTeacher || classTab === 'exams') && (
                <div className="space-y-6">
                  {/* Teacher: Assign New Exam Form */}
                  {isTeacher && (
                    <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#E7E4DC] space-y-3">
                      <h4 className="text-xs uppercase font-bold tracking-wider text-[#16382C] flex items-center gap-2">
                        <FileText size={14} />
                        <span>Assign Exam to This Cohort</span>
                      </h4>

                      {unAssignedExams.length === 0 ? (
                        <p className="text-xs text-[#969E99]">
                          {exams.length === 0 
                            ? 'You have not created any exams yet. Create an exam in Examination Studio first.'
                            : 'All of your created exams are already assigned to this classroom.'}
                        </p>
                      ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-12 gap-2">
                          <div className="sm:col-span-6">
                            <select
                              className="w-full px-3 py-2 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#1C2421] focus:border-[#16382C] outline-none"
                              value={selectedExamToAssign}
                              onChange={(e) => setSelectedExamToAssign(e.target.value)}
                            >
                              <option value="">-- Select exam to assign --</option>
                              {unAssignedExams.map((ex) => (
                                <option key={ex.id} value={ex.id}>
                                  {ex.title} ({ex.total_marks} marks)
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="sm:col-span-3">
                            <input 
                              type="datetime-local"
                              className="w-full px-3 py-2 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#1C2421] focus:border-[#16382C] outline-none"
                              value={assignmentDueDate}
                              onChange={(e) => setAssignmentDueDate(e.target.value)}
                              title="Optional Due Date"
                            />
                          </div>

                          <div className="sm:col-span-3">
                            <Button
                              variant="primary"
                              size="sm"
                              className="w-full"
                              disabled={!selectedExamToAssign}
                              loading={assigningExam}
                              onClick={handleAssignExam}
                              icon={Plus}
                            >
                              Assign Exam
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* List of Assigned Exams */}
                  <div>
                    <h4 className="text-xs uppercase font-bold tracking-wider text-[#969E99] mb-3">
                      Active Assigned Exams
                    </h4>

                    {loadingClassExams ? (
                      <div className="space-y-2">
                        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-16 rounded-xl" />)}
                      </div>
                    ) : classExams.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-[#E7E4DC] rounded-2xl text-xs text-[#969E99]">
                        {isTeacher 
                          ? 'No examinations assigned to this classroom yet. Use the assignment bar above to grant cohort access.'
                          : 'No examinations currently assigned to this classroom.'}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {classExams.map((exam) => (
                          <div 
                            key={exam.id}
                            className="p-4 rounded-xl border border-[#E7E4DC] bg-white hover:bg-[#FAF8F5] flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors"
                          >
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-serif font-bold text-sm text-[#1C2421]">
                                  {exam.title}
                                </span>
                                <Badge tone="sage">{exam.total_marks || 20} Marks</Badge>
                                <Badge tone="neutral">{exam.questions?.length || 0} Questions</Badge>
                              </div>
                              <p className="text-xs text-[#616B66]">
                                Strictness: <strong className="capitalize">{exam.evaluation_strictness || 'Medium'}</strong>
                              </p>
                            </div>

                            <div className="flex items-center gap-2 self-end sm:self-center">
                              {!isTeacher ? (
                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={() => {
                                    handleCloseClass();
                                    if (onStartExam) onStartExam(exam);
                                  }}
                                  icon={ArrowRight}
                                >
                                  Take Exam
                                </Button>
                              ) : (
                                <>
                                  <button
                                    onClick={() => {
                                      handleCloseClass();
                                      if (onViewExam) onViewExam(exam);
                                    }}
                                    className="px-3 py-1.5 rounded-lg border border-[#E7E4DC] text-xs font-semibold text-[#16382C] hover:bg-white cursor-pointer"
                                  >
                                    View Paper
                                  </button>
                                  <button
                                    onClick={() => handleUnassignExam(exam.id, exam.title)}
                                    className="p-1.5 rounded-lg text-rose-600 hover:text-rose-800 hover:bg-rose-50 transition-colors cursor-pointer text-xs"
                                    title="Unassign exam from class"
                                  >
                                    <Trash2 size={15} />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 sm:px-8 py-4 border-t border-[#E7E4DC] bg-[#FAF8F5] flex justify-end">
              <Button variant="outline" size="sm" onClick={handleCloseClass}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Teacher: Create Classroom Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-[#E7E4DC] space-y-5">
            <div className="flex items-center justify-between border-b border-[#F5F2EA] pb-3">
              <h3 className="font-serif text-2xl font-normal text-[#1C2421]">
                Create New Classroom
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="w-7 h-7 rounded-full hover:bg-[#E7E4DC] flex items-center justify-center text-[#616B66] cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateClass} className="space-y-4 text-xs font-sans">
              <div>
                <label className="block text-xs uppercase tracking-wider text-[#969E99] font-medium mb-1">
                  Classroom Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Class 12 Physics - Batch A"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none"
                />
              </div>

              <div>
                <label className="block text-xs uppercase tracking-wider text-[#969E99] font-medium mb-1">
                  Description / Cohort Details
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Physics students preparing for CBSE Term 2 exams"
                  value={newClassDesc}
                  onChange={(e) => setNewClassDesc(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none resize-none"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-[#F5F2EA]">
                <Button variant="outline" size="sm" type="button" onClick={() => setCreateModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" loading={creating}>
                  Create Classroom
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
