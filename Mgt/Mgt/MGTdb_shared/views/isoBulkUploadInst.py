from django.views.generic.base import TemplateView
from django_countries import countries
from django.shortcuts import render

class IsoBulkUploadInst(TemplateView):

	# template_name = "Salmonella/isoBulkUploadInst.html"
 
	def get(self, request, *args, **kwargs):
		org = self.kwargs.get('org')
		print('bulk upload for:', org)
		return render(request, "Templates/isoBulkUploadInst.html", {"organism":org})
		# return ["Templates/isoBulkUploadInst.html"]


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['countries'] = list(countries)
		return context

"""
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['latest_articles'] = Article.objects.all()[:5]
    return context
"""
