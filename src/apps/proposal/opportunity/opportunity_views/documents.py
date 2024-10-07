from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from apps.rental.mixin import CustomDataTableMixin, LoginRequiredMixin

from ..forms import UploadDocumentForm
from ..models import Document, Opportunity


class DocumentListAjaxView(CustomDataTableMixin):
    """AJAX view to list documents in a DataTable format."""

    model = Document

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        stage = self.kwargs.get("stage")
        qs = Document.objects.filter(opportunity__document_number=document_number, stage=stage)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(document_icontains=self.search)
                | Q(comment_icontains=self.search)
                | Q(created_at_icontains=self.search)
            )
        return qs

    def _get_documents(self, obj):
        if obj.document:
            return f"<div class='text-center'><a href='{obj.file_path}' target='_blank' download><i class='icon-cloud-download'></i> {obj.document.name}</a></div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_comments(self, obj):
        if obj.comment:
            return f"<div class='text-center'>{obj.comment}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_created_at(self, obj):
        if obj.created_at:
            created_at = obj.created_at.strftime("%m-%d-%Y")
            return f"<div class='text-center'>{created_at}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "document": self._get_documents(o),
                    "created_at": self._get_created_at(o),
                    "comment": self._get_comments(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class UploadDocument(LoginRequiredMixin, CreateView):
    """
    View to handle document uploads associated with an opportunity.
    """

    model = Document
    form_class = UploadDocumentForm
    template_name = "proposal/file_upload.html"

    def form_valid(self, form):
        """
        Process a valid form submission for document upload.

        :param form: The submitted form with valid data.
        :return: Redirect to the success URL.
        """
        document_number = self.request.POST.get("document_number")
        comment = self.request.POST.get("comment")
        stage = self.request.POST.get("stage")

        # Retrieve the associated Opportunity object
        opportunity_object = get_object_or_404(Opportunity, document_number=document_number)

        # Set form instance attributes
        form.instance.opportunity = opportunity_object
        form.instance.stage = stage
        form.instance.comment = comment

        # Save the document
        form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handle an invalid form submission.

        :param form: The submitted form with errors.
        :return: Render the form with errors.
        """
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Error in {field}: {error}")
        return super().form_invalid(form)

    def get_success_url(self):
        """
        Define the URL to redirect to upon successful document upload.

        :return: The success URL for the opportunity detail view.
        """
        document_number = self.request.POST.get("document_number")
        return reverse("proposal_app:opportunity:opportunity-detail", args=(document_number,))
